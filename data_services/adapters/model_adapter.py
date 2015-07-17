########################################################################################################################
# VECNet CI - Prototype
# Date: 05/02/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
########################################################################################################################

import urllib2
import json
import datetime
import time
import logging
import inspect
import cStringIO

from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q, Sum
from django.db import connections

from data_services.utils.run_data import RunData
from datawarehouse.models import FactWeather
from data_services.models import DimLocation, DimRun, DimExecution, GisBaseTable, DimUser, \
    DimNotes, DimTemplate, DimReplication, DimBaseline

logger = logging.getLogger('prod_logger')

class Model_Adapter(object):
    """
    This is the Model_Adapter class.  It was meant to be used as an abstract base class from which other adapters
    could be based upon.  Common methods to all models should fall into here, and only model specific pieces of
    code should be put in specific model or tool adapters.  The queries here should be optimized eventually in the
    VecNet CI Data Warehouse.
    """
    #: Adapter version
    adapter_version = '1.0-rev$Revision: 5173 $'
    #: User attached to a given instantiation
    user_id = None
    #: Was this user 'new'
    new_user = None
    #: Location of the CSV containin location information and link data
    csv_url = ''
    #: Base URL for downloading files from the digital library
    library_url = 'http://dl-vecnet.crc.nd.edu/downloads/'
    #: Location dictionary describing data locations
    locations_dict = dict()
    #: Filenames dictionary
    filenames = dict()
    #: Default Mosquito Dict, contains default bionomics for mosquitoes
    default_mosq_dict = dict()
    #: Mosquito Bionomics dictionary
    mosquito_dict = dict()
    #: Model id, 1 for EMOD, 2 for OM
    model_id = 0
    #: Template Dictionary
    template_dict = dict()
    #: Xpath for seed, set as '', but needs to be not '' in adapter instance
    seed_path = ''
    #: manifest file object.
    manifest_file = None
    #: Input file list, needs to be set for new models
    inputFiles = None
    #: Default highchart object for use with visualization
    highchart = {
        "chart": {
            "renderTo": "",
            "type": "scatter",
            "inverted": False,
            "zoomType": 'xy',
            "width": 650,
            "height": 650
        },
        "scrollbar": {
            "enabled": True
        },
        "title": {
            "text": ""
        },
        "xAxis": {
            "title":{
                "text": "Days"
            },
            "categories": "",
            "labels":{
                "rotation":270
            }
        },
        "yAxis": {
            "title": {
                "text": ""
            }
        },
        "series": "",
        "exporting": {
            "enabled": True
        },
        "navigation": {
            "buttonOptions": {
                "enabled": True
            }
        },
        "credits": {
            "enabled": True
        }
    }

    EMOD_buffer = cStringIO.StringIO("""Country,Place,Resolution(arcmin),Years,FileUID
Kenya,Nyanza,2.5,20020101-20110101,1n79h4427
Tanzania,Namawala,2.5,19900101-19990101,pc289j04q
Tanzania,Muheza,2.5,20010101-20100101,1n79h441z
Nigeria,Garki,2.5,19710101-19720101,1n79h440p
Solomon Islands,Honiara,2.5,20030101-20330101,wh246s153
Uganda,Tororo,2.5,19950101-20040101,vd66w953h
Vietnam,Binh Long,2.5,19950101-20040101,0c483w01f""")

    OM_buffer = cStringIO.StringIO("""Country,Place,Resolution(arcmin),Years,FileUID
Kenya,Siaya,NA,NA,tt44pm912
Solomon Islands,Solomon Islands,NA,NA,x059c738z""")

    EMOD_buffer.seek(0)
    OM_buffer.seek(0)

    def __init__(self, user_name='Test'):
        """ This is the init method

        This takes a user_name.  The init method will then attempt to look up the user in the DW user table.  If it
        fails to do this, it will create a user, and save the user id to a class variable so it can be used in referenes

        :param user_name: User name of the user for which to fetch data.
        :type user_name: str or unicode
        """
        if not isinstance(user_name, (str, unicode)):
            raise TypeError('User name must be a string or unicode, received %s' % type(user_name))
        user = DimUser.objects.get_or_create(username=user_name)
        self.user = user[0]
        self.new_user = user[1]
        
        # ------------------------------- Re-initialize the immutable data types -------------------------------------#
        self.locations_dict = dict()
        self.filenames = dict()
        self.default_mosq_dict = dict()
        self.mosquito_dict = dict()
        self.template_dict = dict()
        return

    #----------------------------------------- Fetch Methods ---------------------------------------------------------#

    def fetch_locations(self):
        """
        This method is responsible for delivering the list of locations for which we have expert created data.
        This currently grabs a csv file containing information from the Digital Library.  It parses that file
        and then looks through the location data in the Data Warehouse.  If it can't find a match it hides that
        result from the user.
        NOTE: During the last Digital Library outage we moved the file into the adapter itself.

        :returns: Dictionary containing location information where the keys are the location indexes
        """
        # TODO: Raise exceptions instead of returning -1

        try:
            if self.model_id == 1:
                csv = self.EMOD_buffer
            elif self.model_id == 2:
                csv = self.OM_buffer
            # csv = urllib2.urlopen(self.csv_url, timeout=30)  # Creates a "file-like" object containing the csv information
        except urllib2.URLError:
            print "There has been an error retrieving the csv from the meta data catalog"
            return -1

        # Skip the first line, as it contains header information
        contents = csv.readline()

        contents = csv.read().split('\n')

        # If self.location_dict exists, wipe it out
        self.locations_dict.clear()

        for line in contents:
            elements = line.split(',')
            if line == '': continue
            # Find locations and get location id
            loc_filter = DimLocation.objects.filter(
                Q(admin3=elements[1]) |
                Q(admin2=elements[1]) |
                Q(admin1=elements[1]) |
                Q(admin0=elements[1])
            )
            if loc_filter.exists():
                # Takes the first one it finds
                location = loc_filter[0]
            else:
                loc_filter = GisBaseTable.objects.filter(s_name=elements[1])
                if not loc_filter.exists():
                    #Not in our database, so it shouldn't be presented to the tools
                    continue
                contains = GisBaseTable.objects.filter(geom__contains=loc_filter[0].geom)
                geo_dict = {
                    -1: None,
                    0: None,
                    1: None,
                    2: None,
                    3: None
                }
                for geo in contains:
                    geodict[geo.admin_level] = geo.s_name
                location = DimLocation(
                    admin007=geo_dict[-1],
                    admin0=geo_dict[0],
                    admin1=geo_dict[1],
                    admin2=geo_dict[2],
                    admin3=geo_dict[3],
                    geom_key_id=loc_filter[0].id
                )
                location.save()

            if elements[3] == 'NA':
                start_date = ''
                end_date = ''
            else:
                start = elements[3].split('-')[0]
                end = elements[3].split('-')[1]
                start_date = '{0}-{1}-{2}'.format(start[0:4], start[4:6], start[6:8])
                end_date = '{0}-{1}-{2}'.format(end[0:4], end[4:6], end[6:8])

            # Fill the location dictionary
            self.locations_dict[location.id] = {
                "country": elements[0],
                "place": elements[1],
                "resolution": elements[2],
                "start_date": start_date,
                "end_date": end_date,
                "link": self.library_url + elements[4]
            }

            self.EMOD_buffer.seek(0)
            self.OM_buffer.seek(0)

        return self.locations_dict

    def fetch_locations_raw(self):
        """
        This method fetches a complete, hierarchical copy of the dim_locations
        table in the Data Warehouse.
        """
        loc_filter = None
        try:
            # use the raw query because we need the "is not null" feature...
            query = "select * from dim_location where admin007 is not null and admin0!='' order by admin007, admin0, admin1, admin2"
            loc_filter = DimLocation.objects.raw(query)
            dummy = loc_filter[0] # poke the first one, to make sure there is one...
        except:
            loc_filter = None

        return loc_filter

    def fetch_template_list(self, loc_ndx=-1, model_id=-1):
        """
        This is the fetch_template_list method.  It is responsible for fetching the list of templates available to a
        given model.  This only shows the most recent (newest version) of the template.  This should be called before
        fetch_template and used in conjunction with that method.

        :param loc_ndx: (Optional) Location index for which to fetch templates.  This can be found by using the
                        fetch_locations method of this class or left blank to fetch all locations for a given model.
        :type loc_ndx: int
        :param model_id:
        """
        # where_clause = ''
        # # If self.template_dict exists at this point, it should be cleared out
        # if len(self.template_dict.keys()) != 0: self.template_dict.clear()
        # if loc_ndx >= 0:
        #     # This means that it exists
        #     # First we have to check that this loc_ndx is valid
        #     location = DimLocation.objects.filter(pk=loc_ndx)
        #     if not location.exists():
        #         raise ObjectDoesNotExist('No location with id %s could be found' % loc_ndx)
        #     where_clause += ' and location_key=%s' % loc_ndx
        #     # temps = DimTemplate.objects.filter(location_key_id=loc_ndx, model_key_id=(self.model_id if model_id == -1 else model_id))
        # # else:
        #     # temps = DimTemplate.objects.filter(model_key_id=(self.model_id if model_id == -1 else model_id))
        # where_clause += ' and model_key=%s' % (self.model_id if model_id == -1 else model_id)
        # query = "select id, template_name, description, location_key, model_key, user_key " \
        #         "from (select *, row_number() over (partition by template_name order by version DESC) as rn from dim_template) " \
        #         "as foo where rn=1"
        # temps = DimTemplate.objects.raw(query + where_clause)

        # Fetch all public templates, templates ownered by the user or available for this user.
        temps = DimTemplate.objects.filter(Q(user=self.user.id) | Q(user=1) | Q(shared_with=self.user.id),
                                           active=True,
        )
        template_dict = dict()
        for temp in temps:
            file_dict = dict()
            file_return_dict = dict()
            for file in temp.dimfiles_set.all():
                file_dict[file.file_type] = {
                    "name": file.file_name,
                    "description": file.description,
                    "content": file.content
                }
                file_return_dict[file.file_type] = {
                    "name": file.file_name,
                    "description": file.description
                }
            self.template_dict[temp.id] = {
                "name": temp.template_name,
                "description": temp.description,
                "files": file_dict,
                "location_ndx": temp.location_key_id
            }
            template_dict[temp.id] = {
                "name": temp.template_name,
                "description": temp.description,
                "files": file_return_dict,
                "location_ndx": temp.location_key_id
            }
        return template_dict

    def fetch_template(self, template_ndx, file_type=''):
        """
        This is the fetch_template method.  It is responsible for fetching the templates available to a given model.
        This method fetches the contents of the file. This should be run in conjunction with fetch_template_list.

        :param template_ndx:  Index of the template to be fetched, can be found from the output of fetch_template_list
        :type template_ndx: int
        :param file_type: (Optional) The file whose contents will be fetched, for example, config.json, campaign.json,
                          or input.xml or all files for a given template if blank
        :type file_type: str or unicode
        :returns: Dictionary whose keys are the file_type and whose values are string containing the content of the file
        """
        if not isinstance(template_ndx, int):
            raise ValueError('template_ndx should be an integer, received %s' % type(template_ndx))
        if not isinstance(file_type, (str, unicode)):
            raise ValueError('file_type must be string or unicode, received %s' % type(file_type))

        template = DimTemplate.objects.filter(
            # Q(user_id=1) |
            # Q(user_id=self.user.id),
            pk=template_ndx
        )

        if not template.exists():
            raise ObjectDoesNotExist("No template with index %s exists" % template_ndx)

        if file_type is not '':
            file = template[0].dimfiles_set.filter(file_type=file_type)
            if not file.exists():
                raise ObjectDoesNotExist('No file type of %(type)s was found for template %(template)s' % {
                    'type': file_type,
                    'template': template_ndx
                })
            return file[0].content
        else:
            files = template[0].dimfiles_set.all()
            if not files.exists():
                raise ObjectDoesNotExist('Template file issue, template %s has no related files' % template_ndx)
            return_dict = dict()
            for file in files:
                return_dict[file.file_type] = file.content
            return return_dict

    def fetch_keys(self, run_id):
        """
        This is responsible for fetching a set of unique changes that are being applied execution by execution.  This
        will also return the available values for these changes.

        :param run_id: ID of the run for which keys should be fetched
        :type run_id: int
        :returns: A dictionary whose keys are the xpath changes and values are lists of possible values
        :raise: ObjectDoesNotExist
        """
        run = DimRun.objects.get(pk=run_id)
        if not run:
            raise ObjectDoesNotExist('Run with %s not found' % run_id)

        if len(run.dimexecution_set.all()) == 1:
            # If there is only one execution, there are no sweeps
            return list()

        if run.storage_method == 'jcd':
            return self.fetch_keys_jcd(run)

        raise NotImplementedError("hstore-based executions are depricated and no longer supported")

    def fetch_keys_jcd(self, run):
        """
        This is similar to the fetch keys function above.  However, the difference is this will find the sweeps, unique
        keys and values for those sweeps, and return these to the UI.  This is more of an internal call, meaning that
        fetch_keys will call this upon discovering that the JCD method was used to create the run.
        """
        query = "SELECT json_extract_path(jcd, 'Changes') from dim_execution where run_key=%s"

        cursor = connections['default'].cursor()
        cursor.execute(query % run.id)
        results = cursor.fetchall()
        # Added to protect against runs without multiple executions
        if len(results) == 1 and results[0][0] is None:
            return list()
        reses = [tuple(res[0]) for res in results]
        res = zip(*reses)
        retList = list()
        for index in res:
            if isinstance(index[0], dict):
                keySet = set()
                valSet = set()
                for r in index:
                    keySet.update(r.keys())
                    valSet.update(r.values())
                retList.append({keySet.pop(): list(valSet)})
            elif isinstance(index[0], (str, unicode)):
                list(set(index))
            else:
                raise Exception("Unsupported type in execution level JCD")

        return retList


    def fetch_weather_chart(self,loc_ndx,destination='', start_date=None, end_date=None):
        """ This is the fetch_weather_chart method

        This method will eventually take a location index, start and end dates and fetch weather data for these
        selections.

        :param loc_ndx: Index of the location for which to fecth weather for
        :type loc_ndx: int
        :param destination: (Optional) Div in the template for while the chart should be made.  Otherwise you have to
                            instantiate this separately.
        :type destination: str or unicode
        :param start_date: Start date for the data you wish to fetch
        :type start_date: datetime.datetime or string with YYYY-MM-DD format
        :param end_date: End date for the data you wish to fetch
        :type end_date: datetime.datetime or string with YYYY-MM-DD format
        :returns: A list of charts containing weather information
        """
        # Make a copy of the highchart default object
        chart_dict = dict()
        chart_dict['humidity_chart'] = self.highchart.copy()
        chart_dict['rainfall_chart'] = self.highchart.copy()
        chart_dict['mean_temp_chart'] = self.highchart.copy()
        # weather_chart = self.highchart.copy()

        # Now we grab the mean temperature, total_precipitation, and humidity from fact weather.
        # As we only have dew point and temperature in the table, we must calculate relative humidity.
        # To do this we use an approximation found at http://en.wikipedia.org/wiki/Dew_point
        mean_temp = list()
        tot_precip = list()
        humidity = list()
        dates = list()
        series_list = list()

        if start_date is not None and not isinstance(start_date, datetime.datetime):
            start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        if end_date is not None and not isinstance(end_date, datetime.datetime):
            end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d")

        if start_date is not None and end_date is not None:
            days = FactWeather.objects.filter(
                date_key__timestamp__gte=start_date,
                date_key__timestamp__lte=end_date
            ).order_by('date_key__timestamp')
        elif start_date is not None:
            days = FactWeather.objects.filter(date_key__timestamp__gte=start_date).order_by('date_key__timestamp')
        elif end_date is not None:
            days = FactWeather.objects.filter(date_key__timestamp__lte=end_date).order_by('date_key__timestamp')
        else:
            days = FactWeather.objects.filter(date_key__timestamp__gte='1986-05-30').order_by('date_key__timestamp')
            start_date = datetime.datetime.strptime('1986-05-30', "%Y-%m-%d")

        for i, day in enumerate(days):
            # data_list = list()
            # data_list.append(day.mean_temp)
            mean_temp.append(day.mean_temp)
            tot_precip.append(day.total_precip)
            if day.mean_temp >= 9999 or day.mean_dewpnt >= 9999:
                humidity.append(0)
            else:
                humidity.append(100 - 5 * (day.mean_temp - day.mean_dewpnt))

        # series_list.append({
        #     "name": "Mean Temperature",
        #     "data": mean_temp,
        #     "pointStart": time.mktime(datetime.date.timetuple(start_date)) * 1000, # 517816800000,
        #     "pointInterval": 24 * 3600 * 1000
        # })
        chart_dict['humidity_chart']['chart'] = {}
        chart_dict['humidity_chart']['xAxis'] = {"type": 'datetime'}
        chart_dict['humidity_chart']['series'] = [
            {
                "name": "Humidity",
                "data": humidity,
                "pointStart": time.mktime(datetime.date.timetuple(start_date)) * 1000,
                "pointInterval": 24 * 3600 * 1000
            }
        ]
        chart_dict['humidity_chart'] = json.dumps(chart_dict['humidity_chart'])
        chart_dict['mean_temp_chart']['chart'] = {}
        chart_dict['mean_temp_chart']['xAxis'] = {"type": 'datetime'}
        chart_dict['mean_temp_chart']['series'] = [
            {
                "name": "Mean Temperature",
                "data": mean_temp,
                "pointStart": time.mktime(datetime.date.timetuple(start_date)) * 1000,
                "pointInterval": 24 * 3600 * 1000
            }
        ]
        chart_dict['mean_temp_chart'] = json.dumps(chart_dict['mean_temp_chart'])
        chart_dict['rainfall_chart']['chart'] = {}
        chart_dict['rainfall_chart']['xAxis'] = {"type": 'datetime'}
        chart_dict['rainfall_chart']['series'] = [
            {
                "name": "Rainfall",
                "data": tot_precip,
                "pointStart": time.mktime(datetime.date.timetuple(start_date)) * 1000,
                "pointInterval": 24 * 3600 * 1000
            }
        ]
        chart_dict['rainfall_chart'] = json.dumps(chart_dict['rainfall_chart'])

        return chart_dict

    def fetch_runs(self, scenario_id=-1, run_id=-1, loc_ndx=-1, as_object=False, get_All=False, has_data=False):
        """
        This method is responsible for fetching the runs contained by a specific  or a specific run (pending
        on whether run_id is specified.  The as_object flag determined whether a queryset or dictionary is returned.
        get_All determines if 'deleted' runs are returned with non-deleted runs.

        :param run_id: ID of the run to be fetched
        :type run_id: int
        :param as_object: Determines whether a queryset is returned (True) or a dictionary
        :type as_object: bool
        :param get_All: Determines whether 'deleted'  are returned (True) or not (Default)
        :returns: Either a dictionary or a queryset
        :raises: ObjectDoesNotExist
        """

        if scenario_id != -1:
            scenario = DimBaseline.objects.get(id=scenario_id)
            if scenario.user == self.user:
                runs = DimRun.objects.filter(baseline_key=scenario)
        else:
            scenarios = DimBaseline.objects.filter(user=self.user)
            for scenario in scenarios:
                runs = DimRun.objects.filter(baseline_key=scenario)

        if run_id != -1:
            run = DimRun.objects.get(id=run_id)
            if run:
                return run
            else:
                raise ObjectDoesNotExist("Run with id {0} does not exist".format(str(run_id)))

        if not get_All:
            runs = runs.filter(is_deleted=False)

        if loc_ndx != -1:
            runs = runs.filter(location_key_id=loc_ndx)

        if has_data:
            runs = runs.filter(status__isnull=False)

        if as_object:
            return list(runs)
        else:
            run_dict = dict()
            for run in list(runs):
                executions = DimExecution.objects.filter(run_key=run)
                exec_dict = dict()
                for execution in executions:
                    exec_dict[execution.id] = {
                        "name": execution.name
                    }
                run_dict[run.id] = {
                    "name": run.name,
                    "description": run.description,
                    "executions": exec_dict,
                    "time_launched": run.time_launched
                }
                if get_All:
                    run_dict[run.id]['is_deleted'] = run.is_deleted
            return run_dict

    def fetch_params(self, run_id, as_object=False):
        """
        This method is responsible for fetching parameter changes that have been saved by a particular run.  This is
        used to grab the changes so that they can be edited.

        :param run_id: ID of the run for which params should be fetched
        :type run_id: int
        :param as_object: Determines whether a queryset or a list of dictionaries is returned.
        :type as_object: Boolean
        :returns: Either a list of dictionaries (default) or a queryset
        :raises: ObjectDoesNotExist
        """
        # Try to fetch run
        raise NotImplementedError("hstore-based runs are no longer supported")

    def fetch_notes(self, run_id, as_object=False):
        """
        This method is responsible for returning notes attached to a specific scenario

        :param run_id: ID of the run for which notes should be fetched
        :type run_id: int
        :param as_object: Determines whether a queryset or a list of notes (default) is returned
        :type as_object: bool
        :returns: Either a list (default) or a queryset
        :raises: ObjectDoesNotExist
        """
        # Try to fetch the run
        run = DimRun.objects.get(id=run_id)
        if not run:
            raise ObjectDoesNotExist("A run with ID {0} does not exist".format(run_id))
        note_obj = run.dimnotes_set.all()
        if as_object:
            return note_obj
        note_list = list()
        for note in note_obj:
            note_list.append(note.notes)
        return note_list

    def fetch_channels(self, execution_id=-1, run_id=-1, file_name='', as_object=False):
        """ This is the fetch_channels method

        This takes the id of an execution, based on that it looks at the parent run and determines what channels
        there are for this execution.  It then returns either a queryset or a dictionary where the keys are the
        channel ids.  This also has the ability to limit the search by filename (current file names are BinnedReport,
        VectorSpeciesFile, DemographicsSummary, InsetChart, Continuous, Survey).  This also allows the ability to fetch
        channels by run id.
        
        :param execution_id: ID of the execution for which channels should be fetched
        :type execution_id: int
        :param run_id: ID of the run for which channels should be fetched
        :type run_id: int
        :param file_name: The filename, optional search parameter
        :type file_name: str or unicode
        :param as_object: Boolean flag that determines whether a queryset or dictionary is returned.
        :type as_object: bool
        """
        if run_id != -1 and execution_id != -1:
            raise Exception('You must specify either execution_id OR run_id, not both')
        if run_id == -1 and execution_id == -1:
            raise Exception('You must specify either execution_id or run_id')

        if run_id != -1:
            run = DimRun.objects.get(id=run_id)
            if not run:
                raise ObjectDoesNotExist('Run with id %s does not exist' % run_id)
            run = run
        elif execution_id != -1:
            execution = DimExecution.objects.filter(
                pk=execution_id
            )
            if not execution.exists():
                raise ObjectDoesNotExist("Execution with id %s does not exist" % execution_id)
            run = execution[0].run_key
        # replication = DimReplication.objects.filter(execution_key_id=execution_id)[0]
        if file_name is not '':
            channels = run.dimchannel_set.filter(file_name=file_name).order_by('title', 'type')
            if not channels.exists():
                raise ObjectDoesNotExist(
                    'Channel for execution {0} and filename "{1}" do not exist'.format(str(execution_id), file_name)
                )
        else:
            channels = run.dimchannel_set.all().order_by('title', 'type')
        if as_object:
            return channels
        channel_dict = dict()
        for chan_num, chan in enumerate(channels):
            channel_dict[chan.id] = {
                "title": chan.title,
                "type": chan.type,
                "units": chan.units
            }
        return channel_dict

    def fetch_data(self, execution_id=-1, exec_dict=None, run_id=-1, channel_id=-1, as_chart=False, destination='',
                   with_ts=False, channel_name='', channel_type='', as_object=False, as_highstock=False,
                   group_by=False):
        """
        This fetch data method now is an interface for the RunData class.  This will allow the adapter
        to fetch data based on an execution id, channel id, channel name, execution dictionary, etc.  Given
        how flexibile this must be, the RunData class was formed.  This can be simplified by refactoring to
        *kwargs and passing kwargs into RunData

        :param execution_id: Execution id for which data should be fetched
        :type execution_id: int
        :param exec_dict: Dictionary describing an execution
        :type exec_dict: dict
        :param run_id: Constraint on which runs to search for dictionary searching
        :type run_id: int
        :param channel_id: (Optional) Channel id for which data should be fetched
        :type channel_id: int
        :param as_chart: (Optional) Boolean that allows a chart object to be returned or a dictionary
        :type as_chart: bool
        :param destination: (Optional) Div tag that the highstock chart should fill
        :type destination: str or unicode
        :param with_ts: (Defaults False) Boolean that dictates whether an array of timesteps should be returned
                        alongside the data
        :type with_ts: bool
        :param channel_name: (Optional) Name of the channel to be fetched
        :type channel_name: str or unicode
        :param channel_type: (Optional) Type of the channel to be fetched (mosquito type or demographic range)
        :type channel_type: str or unicode
        :param as_object: (Defaults False) Allows a queryset to be returned instead of a dictionary
        :type as_object: bool
        :param group_by: Flag that determines whether to group the data returned by the call into yearly segments
        :type group_by: bool
        """
        arguments = dict()
        if execution_id != -1:
            arguments['execution'] = execution_id
        elif isinstance(exec_dict, (dict, list)):
            arguments['execution'] = exec_dict
            if run_id == -1:
                raise NameError('run_id must be specified if dictionary search is used')
            arguments['run'] = run_id
        if channel_id != -1:
            arguments['channel'] = channel_id
        else:
            if channel_name is '':
                raise NameError('channel_name must be specified if not using channel id')
            arguments['channel'] = {
                'title': channel_name,
                'type': (None if channel_type is '' else channel_type)
            }
        arguments['group_by'] = group_by

        data_obj = RunData(**arguments)

        if as_chart or as_highstock:
            return data_obj.as_chart(as_highstock=as_highstock)
        elif as_object:
            return data_obj.as_object()
        else:
            return data_obj.as_dict(with_ts=with_ts)

    def fetch_geojson(self, **kwargs):
        """
        This method is resposible for fetching geojsons for a given location index or list of location indexes.

        :param location: Should be a single integer or list of integers (or objects castable to integers) referencing
                         location indexes.
        :type location: integer, str, unicode, list
        :returns: a single geojson or a list of tuples (location index, geojson)
        :raises: ObjectDoesNotExist, NameError
        """
        if 'location' not in kwargs and 'run' not in kwargs:
            raise NameError('Keyword location or run must be specified')
        locations = list()
        if 'location' in kwargs:
            if isinstance(kwargs['location'], (int, float, str, unicode)):
                try:
                    locations = DimLocation.objects.filter(pk=int(kwargs['location']))
                except ValueError:
                    raise ValueError('Keyword location must be castable to int, received %s' % type(kwargs['location']))
                if not locations.exists():
                    raise ObjectDoesNotExist('No location with ID %s exists' % kwargs['location'])
            elif isinstance(kwargs['location'], list):
                try:
                    locations = [int(loc) for loc in kwargs['location']]
                except ValueError:
                    raise ValueError('Keyword location list must contain objects castable to int, received %s' % kwargs['location'])
                locations = DimLocation.objects.filter(pk__in=locations)
                if not locations.exists():
                    raise ObjectDoesNotExist('No Location with ID %s exists' % kwargs['location'])
            else:
                raise ValueError(
                    'Keyword location must be an integer, string, unicode, float, or list, received %s' % kwargs['location']
                )
        if 'run' in kwargs:
            if isinstance(kwargs['run'], (int, float, str, unicode)):
                try:
                    runs = DimRun.objects.filter(pk=int(kwargs['run']))
                except ValueError:
                    raise ValueError('Keyword run must be castable ro int, received %s' % type(kwargs['run']))
                if not runs.exists():
                    raise ObjectDoesNotExist('Run with ID %s does not exist' % kwargs['run'])
            elif isinstance(kwargs['run'], list):
                try:
                    runs = [int(run) for run in kwargs['run']]
                except ValueError:
                    raise ValueError('Keyword location list must contain objects castable to int, received %s' % kwargs['run'])
                runs = DimRun.objects.filter(pk__in=runs)
                if not runs.exists():
                    raise ObjectDoesNotExist('Run with ID %s exists' % kwargs['run'])
            else:
                raise ValueError(
                    'Keyword run must be an integer, string, unicode, float or list, received %s' % kwargs['run']
                )
            locations = [run.location_key for run in list(runs)]

        cursor = connections['default'].cursor()
        query = "select ST_AsGeoJson(geom), admin_level from gis_base_table where id in (%s)"
        ids = [str(loc.geom_key) for loc in locations]
        cursor.execute(query % ','.join(ids))
        results = cursor.fetchall()
        return_list = list()
        for ndx, result in enumerate(results):
            params = {
                'name': locations[ndx].name(),
                'admin0': locations[ndx].admin0,
                'admin1': (locations[ndx].admin1 if locations[ndx].admin1 is not None else ''),
                'admin2': (locations[ndx].admin2 if locations[ndx].admin2 is not None else ''),
                'admin3': (locations[ndx].admin3 if locations[ndx].admin3 is not None else ''),
                'admin_level': str(result[1])
            }
            geojson = json.loads(result[0])
            geojson['properties'] = params
            return_list.append((locations[ndx].name(), json.dumps(geojson)))
        # return_list = [(locations[i].name(), res[0]) for i, res in enumerate(results)]
        # for i, res in enumerate(results):
        #     return_list.append(locations[i].id, res[0])

        if len(return_list) == 1:
            return return_list[0][1]
        else:
            return return_list

    #--------------------------------------------------------- Save Methods ------------------------------------------#
    def save_run(self, scenario_id, template_id, start_date, name, description, location_ndx,
                timestep_interval, model_id='', duration=0, end_date='',
                note='', run_id=-1, as_object=False):
        """This is the save_run method
        
        This will create a "run" for a specific user.  It takes as its parameters everything
        needed to create the run, and will return either the run id or the run object as per a
        boolean flag (defaults to returning the id).

        :param run_id:          ID of the run if this is being edited
        :param template_id:     ID of the base template that this run is using
        :param start_date:      Start Date of the simulation in YYYY-MM-DD or a dateime.dateime obj
        :param duration:        Duration of the simulation in days
        :param end_date:        End Date of the simulation, this is used, if given instead of duration
        :param name:            Name of the simulation run
        :param description:     Description of the simulation run
        :param location_ndx:    Index of the location that the run is taking place
        :param version:         Version of the model that is being used
        :param model_id:        ID of the model being used (should be set in self.model_id)
        :param timestep_interval:   Timestep interval in days (fractions allowed)
        :param note:            A note to be attached to the run
        :param as_object:       Returns an object if true, otherwise returns the ID otherwise
                                return An ID of the scenario if saved (-1 if not) or the object as per the as_object flag
        """
        if not self.valid_user():
            raise Exception("No valid user detected, only valid users can save runs")
        if duration == 0 and end_date is '':
            print "You must specify duration or end_date, none were specified"
            return -1
        # Make sure start and end dates are taken care of
        if isinstance(start_date, str):
            # Makes sure that start date is a timestamp, either it can come in that way, or be made by string
            start_date = datetime.datetime(
                    int(start_date.split('-')[0]),
                    int(start_date.split('-')[1]),
                    int(start_date.split('-')[2]))
        startDate = start_date
        if end_date is not '': # rgj: and isinstance(end_date, str):
            if isinstance(end_date, str):
                end_date = datetime.datetime(int(end_date.split('-')[0]), int(end_date.split('-')[1]), int(end_date.split('-')[2]))
        else:
            end_date = start_date + datetime.timedelta(days=duration)
        endDate = end_date

        # Add model_version to the run based on DimTemplate
        my_template = DimTemplate.objects.get(id=template_id)

        # Now we piece together run
        run = DimRun(
            baseline_key_id=scenario_id,
            template_key_id=template_id,
            start_date_key=startDate,
            end_date_key=endDate,
            name=name,
            description=description,
            location_key_id=location_ndx,
            timestep_interval_days=timestep_interval,
            models_key_id=(self.model_id if model_id is '' else model_id),
            model_version=my_template.model_version
        )

        if run_id == -1:
            run.save()
        else:
            run.id = run_id
            run.save()

        if run.id == -1:
            print "An error has occurred, the run was not saved"
            return -1

        # Log when the run was saved and who saved it
        logger.info('Run %s was saved by %s', run.id, inspect.stack()[2][1])
        # Now that we have a run_id

        if note is not '':
            self.save_note(run.id, note)

        if as_object:
            return run
        else:
            return run.id


    def save_note(self, run_id, note):
        """
        This method is responsible for saving notes to the Data Warehouse

        :param run_id: ID of the run for which the note should be linked to
        :type run_id: int
        :param note: String containing the note to be saved
        :type note: str or unicode
        :returns: ID of the note save (integer)
        :raises: Exception
        """
        if not self.valid_user():
            raise Exception("No valid user detected, only valid users can save notes")
        db_note = DimNotes(
            run_key_id=run_id,
            notes = note
        )

        db_note.save()

        return db_note.id

    @classmethod
    def expand_run(cls, run, reps_per_exec):
        """
        This will expand the given run into executions.  An execution is a particular configuration of
        a set of inputs to be used by the models.  This will take the JSON Change Document (JCD) from the
        run given and break it out into execution level and run level changes.

        Here we assume that the run object has a jcd attribute.  If not, the method fails. Eventually a
        jcd field will be part of the run model definition.  At time of writing this is not true.

        Run level changes are changes before a factorable type is defined.  The reason for this is that
        changes after the first factorable type is defined must be applied in order, and therefore belong
        to the execution.

        This will return the number of executions, and the list of executions

        :param run: DimRun object that needs to be expanded
        :param reps_per_exec: Number of replications for generated executions
        :returns: Number of executions, List of saved Executions
        """
        if not hasattr(run, 'jcd'):
            raise ValueError("Run object does not have JCD")

        jcd = run.jcd
        exec_list = list()

        (rl_jcd, num_executions, jcd_list) = jcd.expand()

        if num_executions == 1:
            new_execution = DimExecution(
                run_key=run,
                name=run.name,
                replications=reps_per_exec
            )
            new_execution.save()
            exec_list.append(new_execution)
            return num_executions, exec_list

        for doc in jcd_list:
            new_execution = DimExecution(
                run_key=run,
                name=cls.name_from_sweeps(doc.change_list),
                replications=reps_per_exec,
                jcd=doc
            )
            new_execution.save()
            exec_list.append(new_execution)

        return num_executions, exec_list

    @classmethod
    def name_from_sweeps(cls, iterations):
        """
        This will generate a name for an execution given a single realization of the facorial expansion

        :param iterations: Realization of the factorial expansion
        :type iterations: list
        :returns: Name as a string
        """
        name_list = list()
        for value in iterations:
            if isinstance(value, dict):
                for key, entry in value.iteritems():
                    k = key.split('/')[-1]
                    name_list.append("%s is %s" % (k, entry))

        return ' and '.join(name_list)

    def delete_run(self, run_id):
        """
        This is the delete run method.  This implements a 'soft delete' on the DW side.  It sets the is_deleted flag
        in the DW to true and sets the time_deleted field to now.  This will hide runs from users using the fetch_runs
        method above.

        :param run_id:  Id of the run you wish to delete
        :type run_id: int
        """
        if not self.valid_user():
            raise Exception("No valid user detected")
        run = DimRun.objects.get(id=run_id)
        if not run:
            raise ObjectDoesNotExist("No run with id %s was found" % run_id)

        run.is_deleted = True
        run.time_deleted = datetime.datetime.now()
        run.save()
        return

    def run_status(self, run_id, tuple_list=False):
        """ This is the run status method

        This method takes a run number and will fetch the current state of jobs completed to total jobs (replications)
        
        :param run_id: The run_id for which status is to be fetched
        :type run_id: int
        :param tuple_list: (Optional) Boolean flag to show either the return string or a list of tuple containing the
        execution_id and the number of replications.
        :type tuple_list: bool
        """
        if not self.valid_user():
            raise Exception('No valid users detected, only valid users can query run status')
        run = DimRun.objects.get(id=run_id)
        if not run:
            raise ObjectDoesNotExist("No run with id %s exists" % run_id)

        if tuple_list:
            tuple_list = list()
            executions = run.dimexecution_set.all().order_by('id')
            for execs in executions:
                counter = execs.dimreplication_set.all().count()
                tuple_list.append((execs.id, counter))
            return tuple_list

        launched = DimExecution.objects.filter(
            run_key_id=run_id
        ).count()

        #launched = DimReplication.objects.filter(
        #    execution_key__run_key_id=run_id,
        #    status__isnull=False
        #).count()

        if launched == 0:
            return None

        #total_replications = DimReplication.objects.filter(execution_key__run_key_id=run_id).count()
        total_replications = DimExecution.objects.filter(run_key_id=run_id).aggregate(Sum('replications'))['replications__sum']
        completed_replications = DimReplication.objects.filter(
            status=0,
            execution_key__run_key=run_id
        ).count()

        errored_replications = DimReplication.objects.filter(
            status=-1,
            execution_key__run_key=run_id
        ).count()

        # return '%(completed)s %(total)s %(errored)s' % {
        #     'completed': completed_replications,
        #     'total': total_replications,
        #     'errored': errored_replications
        # }
        return (completed_replications, total_replications, errored_replications)

    def valid_user(self):
        """  This is the validate user method

        This was designed so that other adapters could extend this to check for group permissions to access
        and save runs for them.  It's current usage is to check if the user is public or not.
        """
        if self.user.id == 1:
            return False
        # if not self.user.is_active:
        #     return False
        return True

    def fetch_errors(self, run, as_object=False):
        """
        This method is responsible for getting failed replications that belong to executions that belong to this run
        and sending the replication numbers, and the related error messages.

        :param run: ID of the run for which errors should be fetched
        :type run: int, float, string, unicode, or run instance
        :param as_object: Determines whether a queryset or a list of tuples (replication_id, status_msg)
        :returns: A queryset or a list of tuples
        """
        if not isinstance(run, DimRun):
            run = self.find_run(run)

        reps_with_errors = DimReplication.objects.filter(
            execution_key__run_key=run,
            status=-1
        )

        if as_object:
            return reps_with_errors

        ret_list = [(rep.id, rep.status_text) for rep in reps_with_errors]

        return ret_list

    def find_run(self, run):
        """
        This method is responsible for fetching a specific run given a string, unicode, integer, or float.  This
        checks against the owner of the run to see if the user that was used to instantiate this has the rights
        to see the run.

        :param run: The ID of a run
        :type run: str, unicode, int, or float
        :return: The DimRun object given by the passed in ID
        :raises: ValueError, ObjectDoesNotExist
        """
        if isinstance(run, (int, float, str, unicode)):
            try:
                run_obj = DimRun.objects.filter(id=int(run))
            except ValueError:
                raise ValueError("Run must be a string of integer or an integer, received %s" % run)
            if not run_obj.exists():
                raise ObjectDoesNotExist('Run with id %s does not exist' % run)
            return run_obj[0]
