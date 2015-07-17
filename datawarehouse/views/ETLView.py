from django.contrib.formtools.wizard.views import NamedUrlSessionWizardView
from django.core.files.storage import FileSystemStorage
import os, json, cStringIO, pdb, csv
from VECNet import settings
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from django.db.models.loading import get_model, get_app, get_models
from django.db.models import AutoField, ForeignKey
from VECNet.settings import MEDIA_ROOT
from django.core.files.base import ContentFile
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from lib.decorators import group_required



# remove hardcode to user
# primary key is expected to be an AutoField
# files being saved to server; cron job?

# browser length session? clearsession management command
# call clear sessions?
# error catching
# accept more than just csv?
# test valiudation error
# database column names cannot contain ||
# input column names cannot contain ::


class ETLWizard(NamedUrlSessionWizardView):
    # TODO Add class docstring
    # TODO Add method docstring(s)
    template_name = 'datawarehouse/etl.html'
    file_storage = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'ETL'))

    @method_decorator(group_required("ingestor"))
    def dispatch(self, request, *args, **kwargs):
        """Custom dispatch method to clear session data
        """
        if self.request.path.rpartition('/')[2] == 'upload':
            #self.request.session.clear()
            try:
                del self.request.session["wizard_etl_wizard"]
            except KeyError:
                pass
        return super(ETLWizard, self).dispatch(request, *args, **kwargs)
    
    def get_form(self, step=None, data=None, files=None):
        form = super(ETLWizard, self).get_form(step, data, files)
        if step is not None and data is not None:
            return form
        if self.steps.current == 'downloadMapping':
            obj = {}
            obj['table'] = str(self.storage.data['step_data']['selectTable']['selectTable-tables'][0])
            obj['user'] = "1"
            mapobj = {}
            items = self.get_cleaned_data_for_step('createMap')['mapping'].split(",")
            for item in items:
                tmplist = item.split("::")
                mapobj.update(self.create_mapping_object(tmplist[0], tmplist[1], None, mapobj))
                
            obj['mapping'] = mapobj
            form.fields['content'].initial = json.dumps(obj)
        return form
            
    def get_context_data(self, form, **kwargs):
        context = super(ETLWizard, self).get_context_data(form=form, **kwargs)
        if self.steps.current == 'createMap':
            table = self.get_cleaned_data_for_step('selectTable')['tables']
            context['tableColumns'] = self.create_postgres_fieldlist(table)
            context['inputColumns'] = self.get_input_column_names(self.get_cleaned_data_for_step('upload')['inputFile'])

        return context
    
    def done(self, form_list, **kwargs):
        # Create a file and return it to the user for download
        filename = self.storage.data['step_data']['downloadMapping']['downloadMapping-file_name'][0]
        content = self.storage.data['step_data']['downloadMapping']['downloadMapping-content'][0]
        dlFile = cStringIO.StringIO()
        dlFile.write(content)
        response = HttpResponse(FileWrapper(dlFile), content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=' + filename
        response['Content-Length'] = dlFile.tell()
        dlFile.seek(0)
        # Delete the input file from storage
        path = os.path.join(self.storage.file_storage.location, self.get_cleaned_data_for_step('upload')['inputFile'].name)
        os.remove(path)
        return response
    
    def create_mapping_object(self, key, value, table=None, tmpobj=None):
        # this is necessary because passing mutables as defaults has unexpected behavior
        if tmpobj == None:
            tmpobj = {}
        tmp = []
        if table != None:
            tmpobj['table'] = table
        if "||" in key:
            tmp = key.split("||",2)
            if tmp[0] in tmpobj:
                tmpobj[tmp[0]].update(self.create_mapping_object(tmp[2], value, tmp[1], tmpobj[tmp[0]]))
            else:
                tmpobj[tmp[0]] = self.create_mapping_object(tmp[2], value, tmp[1])
        else:
            tmpobj[key] = value
    
        return tmpobj

    def create_postgres_fieldlist(self, table):
        print table
        # get the fields. location table is special.
        if table == "dim_location":
            tmplist = ["lattitude", "longitude", "admin0", "admin1", "admin2", "admin007"]
        else:
            tmplist = []
            app = get_app('datawarehouse')
            models = get_models(app)
            for mdl in models:
                if mdl._meta.db_table == table:
                    fields = mdl._meta.fields
                    for f in fields:
                        if isinstance(f, ForeignKey):
                            tmptable = f.rel.to._meta.db_table
                            for i in self.create_postgres_fieldlist(tmptable):
                                tmplist.append(str(f.name + "||" + tmptable + "||" + i))
                        elif not isinstance(f, AutoField):
                            tmplist.append(str(f.name))
                    break
        return tmplist
    
    def get_input_column_names(self, f):
        tmp = []
        #try:
        # first save the file to disk, then open using universal csv mode
        fs = FileSystemStorage(location=MEDIA_ROOT)
        tmp = fs.save(str(MEDIA_ROOT + '/' + f.name), ContentFile(f.read()))
        reader = csv.reader(open(tmp, 'rU'), dialect=csv.excel_tab, delimiter=",")
        tmp = reader.next()
        #except:
        #    raise ValidationError("Unable to read columns from the input file. Please make sure it is a comma seperated values (csv) file")
        return tmp
