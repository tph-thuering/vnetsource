
########################################################################################################################
# VECNet CI - Prototype
# Date: 01/27/2015
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app
from change_doc import Change, JCD
from data_services.adapters.EMOD import EMOD_Adapter
from data_services.data_api import EMODBaseline
from data_services.models import DimBaseline, DimModel, DimTemplate, DimUser, Folder
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.formtools.wizard.storage import get_storage
from django.contrib.formtools.wizard.views import NamedUrlSessionWizardView
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from job_services.dispatcher import submit

from vecnet.emod import ClimateDataFile

import ast
import copy
import datetime
import json
import ntpath
import time
from StringIO import StringIO
from urllib2 import urlopen
from zipfile import ZipFile

from lib.templatetags.base_extras import set_notification

# Imports that are internal to the ts_emod app

from ts_emod.models import ConfigData, Species
from ts_emod.forms import named_scenarioCreateByTemplate_forms


class ScenarioCreateByTemplate(NamedUrlSessionWizardView):
    """An extension of django.contrib.formtools.wizard.views.NamedUrlSessionWizardView

    For creating an EMOD Baseline through multiple wizard steps.
    Inputs: config settings from DB rows + user input.
    Outputs: Save Baseline to DB
    """

    def get_template_names(self):
        """ A method to provide the step name/template dictionary """
        TEMPLATES = {"location": "ts_emod/scenarioCreateByTemplate_location.html"}
        return [TEMPLATES[self.steps.current]]

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ The method that accepts a request argument plus arguments, and returns an HTTP response.
            Make sure user is logged in
        """
        return super(ScenarioCreateByTemplate, self).dispatch(request, *args, **kwargs)

    def done(self, form_list, **kwargs):
        """A method that processes all the form data at the end of Wizard

        Save collected data from multiple forms into one DB table (Baseline)
        """

        adapter = EMOD_Adapter(self.request.user.username)

        # populate new scenario with template data
        template_id = self.storage.get_step_data('location')['location-template_id']
        my_name = self.storage.get_step_data('location')['location-name']
        my_description = self.storage.get_step_data('location')['location-description']

        # create a new scenario
        my_scenario = EMODBaseline(
            name=my_name,
            description=my_description,
            model=DimModel.objects.get(model='EMOD'),
            user=DimUser.objects.get_or_create(username=self.request.user.username)[0]
        )

        my_template_obj = DimTemplate.objects.get(id=template_id)

        my_scenario.model_version = my_template_obj.model_version
        my_scenario.template_id = template_id
        my_scenario.template = my_template_obj

        my_scenario.save()

        # populate config
        template_config = ast.literal_eval(my_template_obj.get_file_content('config.json'))
        my_scenario_config = copy.deepcopy(template_config)
        # save the scenario config file
        my_scenario.add_file_from_string('config', 'config.json',
                                         str(my_scenario_config),
                                         description=self.steps.current)

        # populate campaign
        try:
            template_campaign = ast.literal_eval(my_template_obj.get_file_content('campaign.json'))
            my_campaign = str(copy.deepcopy(template_campaign))
        except KeyError:
            # use empty campaign file
            my_campaign = str({"Events": []})

        # save the scenario config file
        my_scenario.add_file_from_string('campaign',
                                         'campaign.json',
                                         my_campaign,
                                         description=self.steps.current)

        #########################
        ### Add default files to scenario

        # todo: stop using template zips, when climate files are available elsewhere
        #print my_template_obj.climate_url

        my_location_zip_link = my_template_obj.climate_url

        # Do we cache zip to temp dir first time, and always access them from there (if they exist)
        # FILE_UPLOAD_TEMP_DIR
        # setup work directory
        #my_directory = os.path.join(settings.MEDIA_ROOT, 'uploads/expert_emod/')
        #my_directory = os.path.join(FILE_UPLOAD_TEMP_DIR, 'ts_emod/')
        #if not os.path.exists(my_directory):
        #    os.makedirs(my_directory)

        #inStream = urllib2.urlopen('http://dl-vecnet.crc.nd.edu/downloads/wh246s153')
        #inStream = urllib2.urlopen('https://dl.vecnet.org/downloads/wh246s153')
        if settings.DEBUG is True:
            now = datetime.datetime.now()
            print now, " DEBUG: getting zip file: ", my_location_zip_link
        url = urlopen(my_location_zip_link)
        zipfile = ZipFile(StringIO(url.read()))

        for zip_file_name in zipfile.namelist():
            if settings.DEBUG is True:
                now = datetime.datetime.now()
                print now, " DEBUG: handling file: ", zip_file_name
            my_file = zipfile.open(zip_file_name)
            my_name = ntpath.basename(zip_file_name)

            # determine which file type this is
            # my_name contains 'demographics' ?  (use compiled, store both?)
            # Honiara_demographics.static.compiled.json Honiara_demographics.json
            """
            'air binary',
            'air json',
            'humidity binary',
            'humidity json',
            'land_temp binary',
            'land_temp json',
            'rainfall binary',
            'rainfall json',

            Honiara_demographics.compiled.json
            Honiara_demographics.json
            Honiara_demographics.static.compiled.json
            Honiara_demographics.static.json
            Honiara_humidity_daily10y.bin
            Honiara_humidity_daily10y.bin.json
            Kenya_Nyanza_2.5arcminhumid_1365118879_climateheader.json
            Honiara_rainfall_daily10y.bin
            Honiara_rainfall_daily10y.bin.json
            Honiara_temperature_daily10y.bin
            Honiara_temperature_daily10y.bin.json
            """
            my_type = None
            if '.md5' in my_name:
                continue
            elif 'demographics' in my_name or 'Demographics' in my_name:
                if 'compiled' in my_name:
                    # use in scenario
                    my_type = 'demographics'
                else:
                    # save to storage (to allow user to see contents)
                    self.storage.extra_data['demographics'] = my_file
            elif '.json' in my_name and '.json.bin' not in my_name:
                # 'json' files
                if 'humid' in my_name:
                    my_type = 'humidity json'
                elif 'rain' in my_name:
                    my_type = 'rainfall json'
                elif 'temp' in my_name or 'tmean' in my_name:
                    my_type = 'air json'
            else:
                # must be a binary file
                if 'humid' in my_name:
                    my_type = 'humidity binary'
                elif 'rain' in my_name:
                    my_type = 'rainfall binary'
                elif 'temp' in my_name or 'tmean' in my_name:
                    my_type = 'air binary'

            if my_type is not None:
                if 'binary' in my_type:
                    my_scenario.add_file_from_string(my_type, my_name,
                                                     my_file.read(),
                                                     description=self.steps.current)
                else:
                    my_scenario.add_file_from_string(my_type, my_name,
                                                     my_file.read(),
                                                     description=self.steps.current)

                # todo: fix to allow separate air and land temp files
                # for now: use same files for air temp and land temp
                if my_type in ('air binary', 'air json'):
                    my_type = my_type.replace('air', 'land_temp')
                    my_scenario.add_file_from_string(my_type, my_name, "no land temp file",
                                                     description=self.steps.current)
        ###  END Zip/Input File handling
        ######################

        try:
            my_id, completed = my_scenario.save()
            set_notification('alert-success', 'The simulation was saved. ', self.request.session)

            # todo: add folder stuff to adapter/EMODBaseline (instead, for now get/save object)
            # #6574 - add the folder that owns this scenario
            if self.storage.get_step_data('location')['folder_id'] != '':
                # see todo: my_scenario.folder = int(self.storage.get_step_data('location')['folder_id'])
                temp = DimBaseline.objects.get(pk=my_scenario.id)
                temp.folder = Folder.objects.get(pk=int(self.storage.get_step_data('location')['folder_id']))
                temp.save()

        except KeyError:
            set_notification('alert-error', 'Error: The simulation was not saved. ', self.request.session)

        # check if user wants to launch, or just save
        if 'edit' in self.storage.data['step_data']['location'] \
           and self.storage.data['step_data']['location']['edit'][0] == '1':
            edit_flag = True
        else:
            edit_flag = False

        # clear out saved form data.
        self.storage.reset()

        if edit_flag:
            return redirect("ts_edit_step", step='config', scenario_id=str(my_id))
        else:
            return redirect("ts_emod_scenario_details", scenario_id=my_id)


    def get_context_data(self, form, **kwargs):
        """Extension of the get_context_data method of the NamedUrlSessionWizardView.

        Select/process data based on which step of the Form Wizard it's called for.

        - Date: passes existing start_date, end_date values or nothing then template will use min and max.
        - Preview gets all wizard step data gathered so far.
        """
        context = super(ScenarioCreateByTemplate, self).get_context_data(form=form, **kwargs)

        context['nav_button'] = "ts_ScenarioCreateByTemplate_step"  # set flag to activate nav menu highlighting

        ######### Start code for specific steps #########

        if self.steps.current == 'location':
            the_request = self.request
            adapter = EMOD_Adapter(self.request.user.username)
            templates = adapter.fetch_template_list()  # get for description

            if 'folder_id' in kwargs.keys():
                context['current_folder'] = kwargs['folder_id']

            # For now: limit list to Solomon and Kenya templates
            templates_a = {}
            templates_b = {}
            templates_c = {}
            templates_d = {}
            templates_e = {}
            templates_garki = {}
            templates_new = {}

            # reorder the templates so Vietnam 1st, Kenya 2nd, Solomon 3rd
            for key in templates.keys():
                if 'Vietnam' in templates[key]['name']:
                    templates_a.update({key: templates[key]})
            for key in templates.keys():
                if 'Kenya' in templates[key]['name']:
                    templates_b.update({key: templates[key]})
            for key in templates.keys():
                if 'Solomon' in templates[key]['name']:
                    templates_c.update({key: templates[key]})
            for key in templates.keys():
                if 'Uganda' in templates[key]['name']:
                    templates_d.update({key: templates[key]})
            for key in templates.keys():
                if 'Bougainville' in templates[key]['name']:
                    templates_e.update({key: templates[key]})
            for key in templates.keys():
                if 'New Location' in templates[key]['name']:
                    templates_new.update({key: templates[key]})
            for key in templates.keys():
                if 'Garki' in templates[key]['name']:
                    templates_garki.update({key: templates[key]})

            pager_size = the_request.POST.get('pager_size')
            if pager_size is None:
                pager_size = 10
            else:
                pager_size = int(pager_size)
            pager_offset = the_request.POST.get('pager_offset')
            if pager_offset is None:
                pager_offset = 0
            else:
                pager_offset = int(pager_offset)

            pager_group = the_request.POST.get('pager_group')
            if pager_group is None:
                pager_group = 0
            else:
                try:
                    pager_group = int(pager_group)
                except TypeError:
                    pager_group = 0

            #scenario_count = scenarios.count()
            template_count = len(templates)
            pager_count = template_count / pager_size
            if template_count % pager_size != 0:
                pager_count += 1

            context['pager_offset'] = pager_offset
            context['pager_size'] = pager_size
            context['pager_group'] = pager_group
            context['pager_count'] = range(1, pager_count + 1)
            context['pager_max'] = pager_count
            context['templates_a'] = templates_a
            context['templates_b'] = templates_b
            context['templates_c'] = templates_c
            context['templates_d'] = templates_d
            context['templates_e'] = templates_e
            context['templates_new'] = templates_new
            context['templates_garki'] = templates_garki
            context['template_count'] = template_count
            context['current_start'] = pager_offset * pager_size + 1
            context['current_stop'] = min(template_count, pager_offset * pager_size + pager_size)
            return context

        return context


## An instance of BaselineWizardView
#
# Use step names/Forms tuple defined in forms file.
scenarioCreateByTemplate = ScenarioCreateByTemplate.as_view(named_scenarioCreateByTemplate_forms,
                                                   url_name='ts_ScenarioCreateByTemplate_step', done_step_name='complete')


def reset_scenario(request):
    """ Method to clear out all wizard settings and redirect user to beginning """
    try:
        del request.session['wizard_baseline_wizard_view']
        if 'scenario' in request.session.keys():
            del request.session['scenario']
        if 'scenario_config' in request.session.keys():
            del request.session['scenario_config']
        set_notification('alert-success', 'The simulation was not saved, the settings were cleared. ', request.session)
    except KeyError:
        pass
    return redirect("ts_scenario_step", step='location')


def cancel_edit(request):
    """ Method to cancel editing a scenario, clear out all wizard settings and redirect user to scenario list """
    try:
        del request.session['wizard_baseline_wizard_view']
        if 'intervention_id' in request.session.keys():
            del request.session['intervention_id']
        if 'scenario' in request.session.keys():
            del request.session['scenario']
        if 'scenario_config' in request.session.keys():
            del request.session['scenario_config']
        if 'scenario_template_config' in request.session.keys():
            del request.session['scenario_template_config']

        set_notification('alert-success',
                         'Editing has been canceled.',
                         request.session)
    except KeyError:
        pass
    return redirect("ts_emod_scenario_browse")


def get_chart(request, scenario_id=None, file_type=None):
    # verify that scenario_id is good
    if scenario_id is None or file_type is None:
        return

    # get the scenario
    #my_scenario = DimBaseline.objects.get(id=scenario_id)  # Objects returned here don't have get_file_by_type
    my_scenario = EMODBaseline.from_dw(pk=scenario_id)

    # get the scenario's file of the given type
    # 'air binary',
    # 'humidity binary',
    # 'rainfall binary',
    my_file_json = my_scenario.get_file_by_type(file_type + ' json')
    my_file_bin = my_scenario.get_file_by_type(file_type + ' binary')

    my_chart = getChartData(my_file_json.content, my_file_bin.content)

    # put series into dict
    chart_dict = {"title": {"text": ""}, "series": [{"data": my_chart}]}

    return HttpResponse(json.dumps(chart_dict), mimetype="application/json")


def getChartData(jsonFile, binFile):
    climateDataFile = ClimateDataFile()
    climateDataFile.load(jsonFile, binFile)
    dates = climateDataFile.getDates()
    firstNode = climateDataFile.nodeIDs[0]

    node = []
    count = 0
    for dataPoint in climateDataFile.climateData[firstNode]:
        node.append([])
        timeStamp = dates[count]
        timeStamp = time.mktime(datetime.datetime.strptime(str(timeStamp), "%m/%d/%Y").timetuple())*1000
        node[count].append(timeStamp)
        node[count].append(climateDataFile.climateData[firstNode][count])
        count += 1

    return node
