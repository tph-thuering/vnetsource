__author__ = 'lselvy'

from data_services.models import BaseFactData, DimExecution, DimRun, DimReplication, DimChannel
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.query import QuerySet
import json
import time
import itertools

class RunData(object):
    """
    This is the RunData Class.  As accessing the run results in the VecNet CI data warehouse becomes more and more
    complicated, we decided to split the run data into its own class.  This class handles defining which data you
    want to get, aggregation calls, and the finally reporting the data.
    """

    run = None
    execution = None
    is_queryset = False
    channel = None
    is_channel_queryset = False
    data_results = {}
    qs = list()

    def __init__(self, **kwargs):
        """
        This is the initialization method for the RunData class.  It can take a myriad of arguments and from those it
        will do its best to understand which execution you are talking about, grab and aggregate across that execution,
        and then you can return data from it.

        :param execution: This can be a saved DimExecution instance, an int or float containing the execution ID
                          number, a dictionary containing specific key value pairs or lists of values for a given key,
                          or a string containing the execution ID, or a list of execution ids, or a queryset of objects.
        :type execution: int, float, DimExecution, dict, str, list, queryset
        """
        self.run = None
        self.execution = None
        self.is_queryset = False
        self.channel = None
        self.is_channel_queryset = False
        self.data_results = {}
        self.qs = list()
        if 'execution' in kwargs:
            if isinstance(kwargs['execution'], DimExecution):
                self.execution = kwargs['execution']
                self.run = self.execution.run_key
            elif isinstance(kwargs['execution'], (int, float)):
                execs = DimExecution.objects.filter(pk=int(kwargs['execution']))
                if not execs.exists():
                    raise ObjectDoesNotExist('Execution with id %s does no exist' % int(kwargs['execution']))
                self.execution = execs[0]
                self.run = execs[0].run_key
            elif isinstance(kwargs['execution'], list):
                if not 'run' in kwargs:
                    raise NameError('execution dictionary requires a run to be specified')
                if isinstance(kwargs['run'], (int, float)):
                    run_id = int(kwargs['run'])
                elif isinstance(kwargs['run'], DimRun):
                    run_id = kwargs['run'].id
                elif isinstance(kwargs['run'], (str, unicode)):
                    try:
                        run_id = int(kwargs['run'])
                    except ValueError:
                        raise ValueError('run as a string must be convertible to int')
                else:
                    raise TypeError('run must be an int, float, str, unicode, or DimRun instance')

                runs = DimRun.objects.filter(pk=run_id)
                if not runs.exists():
                    raise ObjectDoesNotExist('run with id %s does not exist' % run_id)
                self.run = runs[0]
                if self.run.storage_method == 'jcd':
                    self.execution = self.executionFromDictionary_jcd(kwargs['run'], kwargs['execution'])
                elif self.run.storage_method == 'hstore':
                    raise NotImplementedError("hstore-based executions are depricated")
                #self.run = self.execution[0].run_key
            elif isinstance(kwargs['execution'], (str, unicode)):
                try:
                    pk = int(kwargs['execution'])
                except ValueError:
                    raise ValueError('Expected execution string to by an integer')
                execs = DimExecution.objects.filter(pk=pk)
                if not execs.exists():
                    raise ObjectDoesNotExist('Execution with id %s does not exist' % pk)
                self.execution = execs[0]
                self.run = execs[0].run_key
            elif isinstance(kwargs['execution'], list):
                try:
                    id_list = [int(id) for id in kwargs['execution']]
                except ValueError:
                    raise ValueError('execution id list must contain integers, strings of integers, or floats')
                execs = DimExecution.objects.filter(pk__in=id_list)
                if not execs.exists():
                    raise ObjectDoesNotExist('No execution with ids %s exist' % str(id_list))
                self.is_queryset = True
                self.execution = execs
                # Assume that all executions belong to a single run
                self.run = execs[0].run_key
            elif isinstance(kwargs['execution'], QuerySet):
                self.execution = kwargs['execution']
                self.run = kwargs['execution'][0].run_key
                self.is_queryset = True
            else:
                raise TypeError(
                    'execution must be an int, float, DimExecution instance, dictionary, or string, received %s'
                    % type(kwargs['execution'])
                )
        else:
            raise NameError('execution keyword was not specified, it is required.')

        if 'channel' in kwargs:
            if isinstance(kwargs['channel'], (int, float)):
                chans = DimChannel.objects.filter(pk=int(kwargs['channel']))
                if not chans.exists():
                    raise ObjectDoesNotExist('Channel with id %s does not exist' % int(kwargs['channel']))
                self.channel = chans[0]
            elif isinstance(kwargs['channel'], list):
                try:
                    id_list = [int(id) for id in kwargs['channel']]
                except ValueError:
                    raise ValueError('channel id list must contain integers, strings of integers, or floats')
                chans = DimChannel.objects.filter(pk__in=id_list)
                if not chans.exists():
                    raise ObjectDoesNotExist('Channels with ids %s do not exist' % str(id_list))
                self.channel = chans
                self.is_channel_queryset = True
            elif isinstance(kwargs['channel'], QuerySet):
                self.is_channel_queryset = True
                self.channel = kwargs['channel']
            elif isinstance(kwargs['channel'], dict):
                try:
                    title = kwargs['channel']['title']
                    # Can't use type as variable name, it shadows built-in name 'type'
                    type0 = kwargs['channel']['type']
                except KeyError:
                    raise KeyError('Channel dictionary must have "title" and "type" keys, received %s' % str(kwargs['channel']))
                chans = DimChannel.objects.filter(
                    title=title,
                    type=type0,
                )
                if not chans.exists():
                    raise ObjectDoesNotExist('Channel with title %(title)s and type %(type)s does not exist' % kwargs['channel'])
                self.channel = chans[0]
            # TODO Channel tuple
            else:
                raise TypeError(
                    'channel must be an int, float, DimChannel instance, dictionary, list, or queryset, received %s' %
                    type(kwargs['channel'])
                )
        else:
            raise NameError('channel keyword was not specified, it is required')

        if 'group_by' in kwargs:
            if not isinstance(kwargs['group_by'], bool):
                raise ValueError('group_by was expected to be a boolean, received %s' % type(kwargs['group_by']))
            if self.run.timestep_interval_days > 365:
                raise ValueError('group_by cannot be invoked if the timestep interval in days is greater than 365 it is %s' % self.run.timestep_interval_days)
            self.is_grouped = kwargs['group_by']
        else:
            self.is_grouped = False


    def executionFromDictionary_jcd(self, run_id, exec_dict):
        iterlist = list()
        for obj in exec_dict:
            if isinstance(obj, list):
                iterlist.append(list)
            elif isinstance(obj, dict):
                iterlist.append(obj.values()[0])
        prods = itertools.product(*iterlist)
        exec_list = list()
        for iteration in prods:
            e_list = list()
            for ndx, obj in enumerate(exec_dict):
                if isinstance(obj, dict):
                    key = obj.keys()[0]
                    try:
                        value = int(iteration[ndx])
                    except ValueError:
                        try:
                            value = float(iteration[ndx])
                        except ValueError:
                            value = iteration[ndx]
                    e_list.append({key: value})
                elif isinstance(obj, list):
                    e_list.append(iteration[ndx])
            exec_list.append(json.dumps(e_list))
        executions = DimExecution.objects.filter(run_key_id=run_id).extra(
            where=["json_extract_path(jcd, 'Changes')::text in ('%s')" % "','".join(exec_list)]
        )

        self.is_queryset = True
        return executions

    def channelFromDict(self, chan_dict):
        """
        This method takes a dictionary and returns a channel instance that this dictionary defines.  It should have
        title and type keys.

        :param chan_dict: Dictionary containing title and type keys that define a channel
        :type chan_dict: dict
        """
        if not 'title' in chan_dict:
            raise KeyError('title is a required key in the channel dictionary, received %s' % str(chan_dict))
        if not 'type' in chan_dict:
            raise KeyError('ype is a required key in the channel dictionary, received %s' % str(chan_dict))

        chans = DimChannel.objects.filter(
            title=chan_dict['title'],
            type=chan_dict['type']
        )

        if not chans.exists():
            raise ObjectDoesNotExist('Channel with title %(title)s and type %(type)s does not exist' % chan_dict)

        return chans[0]

    def aggregate_data(self):
        """
        This method will fetch and aggregate data from the BaseFactData table in the VecNet CI.  This takes the
        executions and channels that are saved in the class, and will create a dictionary that houses the data.

        :returns: A dictionary where the keys are execution names and the values are lists of data.  Another key named
                  'timestep' will also be included that contains timestep information.  This timestep key can be used
                  to fill in the highchart/highstock javascript dates.
        """

        #----------- Determine which query to run
        if self.is_grouped:
            query = """
            select sum(value) as value, row_number() over (order by timestep/%(ts_year)s) as id, (row_number() over (order by timestep/%(ts_year)s)) - 1 as timestep
            from (select distinct(timestep), row_number() over (order by timestep nulls last) as id, avg(value) as value
                from fact_data_run_%(run_id)s
                inner join dim_channel on channel_key=dim_channel.id
                inner join dim_replication on replication_key=dim_replication.id
            where execution_key=%(execution_key)s and dim_channel.id=%(channel_key)s
            group by timestep order by timestep) foo
            group by timestep/%(ts_year)s order by timestep/%(ts_year)s;
            """
            ts_year = self.calculate_year()
        else:
            query = """
            select distinct(timestep), row_number() over (order by timestep nulls last) as id, avg(value) as value
                from fact_data_run_%(run_id)s
                inner join dim_channel on channel_key=dim_channel.id
                inner join dim_replication on replication_key=dim_replication.id
            where execution_key=%(execution_key)s and dim_channel.id=%(channel_key)s
            group by timestep order by timestep
            """
            ts_year = None
        if self.is_queryset and not self.is_channel_queryset:
            for execution in self.execution:
                query_dict = {
                    'run_id': self.run.id,
                    'execution_key': execution.id,
                    'channel_key': self.channel.id,
                    'ts_year': ts_year
                }
                self.qs = list(BaseFactData.objects.raw(query, query_dict))
                if execution.name == '':
                    name = str(execution.id)
                else:
                    name = execution.name
                self.data_results[name] = [point.value for point in self.qs]
            self.data_results['timestep'] = [point.timestep for point in self.qs]
            return
        elif not self.is_queryset and not self.is_channel_queryset:
            query_dict = {
                'run_id': self.run.id,
                'execution_key': self.execution.id,
                'channel_key': self.channel.id,
                'ts_year': ts_year
            }
            self.qs = list(BaseFactData.objects.raw(query, query_dict))
            if self.execution.name == '':
                name = str(self.execution.id)
            else:
                name = self.execution.name
            self.data_results[name] = [point.value for point in self.qs]
            self.data_results['timestep'] = [point.timestep for point in self.qs]
            return
        elif not self.is_queryset and self.is_channel_queryset:
            for chan in self.channel:
                query_dict = {
                    'run_id': self.run.id,
                    'execution_key': self.execution.id,
                    'channel_key': chan.id,
                    'ts_year': ts_year
                }
                self.qs = list(BaseFactData.objects.raw(query, query_dict))
                key = '%(exec_name)s-%(title)s-%(type)s' % {
                    'run_id': self.run.id,
                    'exec_name': self.execution.name,
                    'title': chan.title,
                    'type': chan.type
                }
                self.data_results[key] = [point.value for point in self.qs]
            self.data_results['timestep'] = [point.timestep for point in self.qs]
            return
        elif self.is_queryset and self.is_channel_queryset:
            raise NotImplemented('A queryset of both channels and executions is not yet implemented')

    def calculate_year(self):
        """
        This method will determine how many timesteps there are in a year given the timestep interval in days stored
        in the run.
        """
        DAYS_IN_YEAR = 365
        time_interval = self.run.timestep_interval_days
        mod = DAYS_IN_YEAR % time_interval

        if mod == 0:
            return DAYS_IN_YEAR/time_interval
        elif mod/float(time_interval) >= 0.5:
            return (DAYS_IN_YEAR/time_interval) + 1
        elif mod/float(time_interval) < 0.5:
            return DAYS_IN_YEAR/time_interval
        else:
            raise Exception("Should not have gotten to this point in the code")

    def as_chart(self, as_highstock=False):
        """
        This method is one method responsible for formatting the run data into a highstock or highchart format.  This
        will also convert the timesteps into milliseconds from the epoch (for highstock charts).

        :param as_highstock: Flag that decides whether the json returned is a highstock or highchart object
        :type as_highstock: bool
        :returns: A json object containing a highstock or highchart object
        """
        if not self.data_results:
            self.aggregate_data()
        highchart = {
            "chart": {
                "type": "scatter",
                "inverted": False,
                "zoomType": 'xy',
                "width": 650,
                "height": 650
            },
            "scrollbar": {
                "enabled": True
            },
            "tooltip": {
                "enabled": "false",
                "pointFormat": "<span style=\"color:{series.color}\"> {series.name} </span> : <b>{point.y:,.4f}</b><br/> "
            },
            "legend": {
                "enabled": "true"
            },
            "title": {
                "text": ""
            },
            "xAxis": {
                "title": {
                    "text": "Days"
                },
                "categories": "",
                "labels": {
                    "rotation": 270
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

        start_time = self.run.start_date_key
        interval = getattr(self.run, 'timestep_interval_days', 1)
        #interval = self.run.timestep_interval_days

        if as_highstock:
            return_chart = highchart
            return_chart['chart'] = {}
            return_chart['xAxis'] = {"type": 'datetime'}
            return_chart['series'] = list()

            if self.is_grouped:
                pinterval = 24 * 3600 * 1000 * interval * int(365/interval)
            else:
                pinterval = 24 * 3600 * 1000 * interval

            for key, data in self.data_results.iteritems():
                if key is 'timestep': continue
                return_chart['series'].append({
                    "name": key,
                    "data": data,
                    "pointStart": time.mktime(start_time.timetuple()) * 1000,
                    "pointInterval": pinterval
                })

            return json.dumps(return_chart)

        else:
            return_chart = highchart
            return_chart['xAxis']['categories'] = self.data_results['timestep']
            if not self.is_channel_queryset:
                return_chart['yAxis']['title'] = '{0}-{1}'.format(self.channel.title, self.channel.type)
                return_chart['title'] = "%s vs Timestep" % self.channel.title
            return_chart['series'] = list()
            for key, data in self.data_results.iteritems():
                if key is 'timestep': continue
                return_chart['series'].append({
                    "name": key,
                    "data": data
                })
            return json.dumps(return_chart)

    def as_dict(self, with_ts=False):
        """
        The as_dict method will return the data from the aggregation in the form of a dictionary.  This method should
        be used when passing data to other adapters or programs that need to operate on the data.  This is in contrast
        to the as_chart method, which is for programs that are meant to output the data immediately.

        :param with_ts:  This is a boolean flag that determines whether the timestep is returned with the data or not
        :type with_ts: int
        :returns: A dictionary containing the information requested.
        """
        if not self.data_results:
            self.aggregate_data()

        return_dict = self.data_results.copy()

        if not with_ts:
            return_dict.pop('timestep', None)

        return return_dict
    
    def as_object(self):
        """
        The as object method will return a queryset of BaseFactData.

        :returns: HStoreQueryset
        """
        if not self.data_results:
            self.aggregate_data()
        return self.qs
