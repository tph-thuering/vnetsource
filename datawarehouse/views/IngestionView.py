########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################
"""This is the view used to ingest data.

This view is called to render, as well as process, the ingestion form.
"""

import json
import csv

from django.views.generic import FormView

from django.shortcuts import render
from django.db import connections, IntegrityError
from django.db.models.loading import get_app, get_models
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

from datawarehouse.forms.ETLForms import IngestionForm

from data_services.models import DimLocation, DimUser, GisBaseTable
from datawarehouse.exceptions.etlExceptions import TableDoesNotExist
from VECNet.settings import MEDIA_ROOT

from django.utils.decorators import method_decorator
from lib.decorators import group_required

class IngestionView(FormView):
    """
    This class defines the ingestion view. It inherits Django's generic 'FormView'.
    """
    
    template_name = 'datawarehouse/ingestion.html'
    form_class = IngestionForm
    
    @method_decorator(group_required("ingestor"))
    def dispatch(self, *args, **kwargs):
        """The main entry point for the view. It requires the user to
        be in the Ingestor group.

        :param *args: Argument list.
        :param **kwargs: Keyword argument list.
        """
        return super(IngestionView, self).dispatch(*args, **kwargs)
    
    def form_valid(self, messages):
        """Method called upon successful form validation.

        This method is called when a form is determined to be valid.
        It adds a message to the context, and then renders the template with
        the message.

        :param message: An error or success message, depending on the status
        of ingestion.
        :return: An http repsonse object.
        """
        ctx = {}
        ctx['messages'] = messages
        ctx['form'] = IngestionForm()
        return render(self.request, self.template_name, ctx)
    
    def post(self, request, *args, **kwargs):
        """This method is called when a form is posted.

        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity. Calls the custom ingest
        function if the form is valid.

        :param request: The http request object.
        :param *args: Argument list.
        :param **kwargs: Keyword argument list.
        :return: An http response object, via another method.
        """
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.ingestData(self.request.FILES['inputFile'], self.request.FILES['mappingFile'])
        else:
            return self.form_invalid(form)
    
    def ingestData(self, inputFile, mappingFile):
        """This method is used to ingest data into the database.

        This method is responsible for taking an input file
        and a mapping file and ingesting the data from the input file
        into the database, using the mapping file to determine the
        relationship between input and database columns.

        :return: An http response object via the form_valid method.
        """
        # load the mapping file to json, and read the inputfile using python csv
        f = inputFile        
        m = mappingFile.read()
        data = json.loads(m)
        # first save the file to disk, then open using universal csv mode
        fs = FileSystemStorage(location=MEDIA_ROOT)
        tmp = fs.save(str(MEDIA_ROOT + '/' + f.name), ContentFile(f.read()))
        reader = csv.reader(open(tmp, 'rU'), dialect=csv.excel_tab, delimiter=",")
        # initialize variables
        cols = {}
        row = []
        table = None
        user = None
        sql_dict = {}
        model = None
        counter = 0
        error_list = {}
        
        try:
            for r in reader:
                row = []
                # Build the row dictionary using columns from the file to be ingested
                if counter == 0:
                    c = 0
                    for col_header in r:
                        cols[col_header] = c
                        c = c + 1
                # Load row dictionary with the values of this line
                else:
                    for item in r:
                        row.append(item)
                    # Loop through the mapping for each row
                    for k, v in data.iteritems():
                        if k == 'table':
                            table = v
                        elif k == 'user':
                            user = v
                        elif k == 'mapping':
                            for key, value in v.iteritems():
                                if key == 'location_key':
                                    sql_dict[key] = self.locationMap(value, row, cols)
                                elif isinstance(value, unicode):
                                    sql_dict[key] = row[cols[value]]
                                else:
                                    sql_dict[key] = self.fkeymap(value, row, cols)
        
                    app = get_app('datawarehouse')
                    models = get_models(app)
                    # find the specified model and insert/update it
                    for mdl in models:
                        if mdl._meta.db_table == table:
                            model = mdl
                            break
                    # if a model for the given table couldn't be found, raise an exception
                    if model == None:
                        raise TableDoesNotExist("The database table " + table + " does not exist.")
                    else:
                        sql_dict['user_key'] = DimUser.objects.get(pk=1)
                        try:
                            model, created = model.objects.get_or_create(**sql_dict)
                        except Exception as e:
                            error_list['Row ' + str(counter)] = str(e)
                counter += 1
                
        except (IntegrityError, ObjectDoesNotExist, TableDoesNotExist) as e:
            return self.form_valid({'Message': 'row' + str(counter) + ', ' + str(e)})
        else:
            if error_list == {}:
                error_list['Message'] = "The file was successfully ingested."
            return self.form_valid(error_list)

    def locationMap(self, obj, row, cols):
        """This method is used to map the location key.

        Due to the complicated nature of gis data, a custom method was necessary
        to handle location fields. This method is responsible for ingesting location data
        into the database. It relies on Django's raw query capabilities.

        :return: A DimLocation object.
        """
        
        tmpdict = {}
        # if lattitude and longitude were given, use a stored procedure to find the location
        # containing the given lat/lon. Return the corresponding location, creating it if necessary.
        if 'lattitude' in obj and 'longitude' in obj:
            # Note this hasn't been tested yet (no test cases are available for ingestor)
            return DimLocation.vecnet_fill_location_from_point(row[cols[obj['lattitude']]], row[cols[obj['longitude']]])

            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # Query below (SELECT vecnet_fill_location_from_point) will no longer works after removing
            # partition on gis_base_table. Stored procedure vecnet_fill_location_from_point assumes that
            # gis_adm_007, gis_adm_0lev and other tables exist.
            # This query can be replaced with
            # SELECT * FROM gis_base_table WHERE ST_CONTAINS(geom, ST_GeomFromText('point(%s %s)', 4326));
            # There are no test cases for ingester yet to update the code
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            # conn = connections['default']
            # cursor = conn.cursor()
            # cursor.execute("SELECT vecnet_fill_location_from_point(%s, %s);", [row[cols[obj['lattitude']]], row[cols[obj['longitude']]]])
            # tmp = cursor.fetchone()
            # tmpstr = tmp[0][2:][:-1]
            # tmplist = tmpstr.split(',')
            # tmpdict['geom_key'] = tmplist[0]
            # tmpdict['admin007'] = tmplist[1]
            # tmpdict['admin0'] = tmplist[2]
            # tmpdict['admin1'] = tmplist[3]
            # tmpdict['admin2'] = tmplist[4]
            # model, created = DimLocation.objects.get_or_create(**tmpdict)
            # conn.close()
            # return model
        # if lat/lon wasn't given, use the admin levels to determine the location. Create a
        # location object if necessary, and return the location object.
        else:
            if 'admin2' in obj:
                # Could be replaced with
                # GisBaseTable.object.get(s_name=row[obj['admin2']], admin_level = 2)
                # Double-check admin_level though
                gisobj = GisBaseTable.objects.get(s_name=row[cols[obj['admin2']]], admin_level=2)
                tmpdict['geom_key'] = gisobj.id
                tmpdict['admin2'] = gisobj.s_name
            elif 'admin1' in obj:
                gisobj = GisBaseTable.objects.get(s_name=row[cols[obj['admin1']]], admin_level=1)
                tmpdict['geom_key'] = gisobj.id
                tmpdict['admin1'] = gisobj.s_name
            elif 'admin0' in obj:
                gisobj = GisBaseTable.objects.get(s_name=row[cols[obj['admin0']]], admin_level=0)
                tmpdict['geom_key'] = gisobj.id
                tmpdict['admin0'] = gisobj.s_name
            elif 'admin007' in obj:
                gisobj = GisBaseTable.objects.get(s_name=row[cols[obj['admin007']]], admin_level=-1)
                tmpdict['geom_key'] = gisobj.id
                tmpdict['admin007'] = gisobj.s_name
            model, created = DimLocation.objects.get_or_create(**tmpdict)
            return model
    
    def fkeymap(self, obj, row, cols):
        """This method is used to map a foreign key.

        This method is responsible for recursively fetching and
        returning the necessary foreign key objects to ingest a foreign key
        into the database. 

        :return: A model object.
        """
        
        model = None
        app = get_app('datawarehouse')
        models = get_models(app)
        # attempt to match the specified table to a model and raise an exception if not found
        for m in models:
            if m._meta.db_table == obj['table']:
                model = m
                break
        if model == None:
            raise TableDoesNotExist("The database table " + obj['table'] + " does not exist.")
        
        sql_dict = {}
        # loop through the mapping object and create the object using data from the input file
        # if the value is an object, recursively call fkeymap. 
        for key, value in obj.iteritems():
            if key != 'table':
                if isinstance(value, unicode):
                    sql_dict[key] = (None if row[cols[value]] is "" else row[cols[value]]) 
                else:
                    sql_dict[key] = (None if self.fkeymap(value, row, cols) is "" else self.fkeymap(value, row, cols))
        m, created = model.objects.get_or_create(**sql_dict)
        return m