
########################################################################################################################
# VECNet CI - Prototype
# Date: 03/07/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app
from change_doc import Change, JCD
from data_services.adapters.EMOD import EMOD_Adapter
from data_services.data_api import EMODBaseline
from data_services.models import DimModel, DimTemplate, DimUser, DimRun
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
from ts_emod.forms import named_baseline_forms


class BaselineWizardView(NamedUrlSessionWizardView):
    """An extension of django.contrib.formtools.wizard.views.NamedUrlSessionWizardView

    For creating an EMOD Baseline through multiple wizard steps.
    Inputs: config settings from DB rows + user input.
    Outputs: Save Baseline to DB
    """

    def get_template_names(self):
        """ A method to provide the step name/template dictionary """
        TEMPLATES = {"location": "ts_emod/scenario/location.html",
                     "config": "ts_emod/scenario/config.html",
                     "climate": "ts_emod/scenario/climate.html",
                     "demographic": "ts_emod/scenario/demographic.html",
                     "species": "ts_emod/scenario/species.html",
                     "parasite": "ts_emod/scenario/parameters_shared.html",
                     "scaling_factors": "ts_emod/scenario/scaling_factors.html",
                     "calibration": "ts_emod/scenario/calibration.html",
                     "run": "ts_emod/scenario/run.html",
                     "review": "ts_emod/scenario/review.html"}
        return [TEMPLATES[self.steps.current]]

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ The method that accepts a request argument plus arguments, and returns an HTTP response.
            Make sure user is logged in
        """

        # add the storage engine to the current wizardview instance here so we can act on storage here
        self.prefix = self.get_prefix(*args, **kwargs)
        self.storage = get_storage(self.storage_name, self.prefix, request, getattr(self, 'file_storage', None))

        if 'scenario_id' in kwargs:
            if kwargs['scenario_id'] == '0':
                # first visit to "Add a New Baseline"
                #  wipe out any previous session-scenario and wizard storage (including edit flag).
                try:
                    self.storage.reset()
                except AttributeError:
                    pass
                if 'scenario' in self.request.session.keys():
                    del self.request.session['scenario']
                if 'scenario_config' in self.request.session.keys():
                    del self.request.session['scenario_config']
                # create empty scenario
                self.request.session['scenario'] = EMODBaseline(
                    name='',
                    description='',
                    model=DimModel.objects.get(model='EMOD'),
                    user=DimUser.objects.get_or_create(username=self.request.user.username)[0]
                )
                self.request.session['scenario'].model_version = 'emod'  # set dummy, will be overwritten
            elif kwargs['scenario_id'] > 0:
                # First hit in Edit mode - populate the steps with initial defaults
                self.storage.reset()
                self.storage.extra_data['edit_scenario'] = kwargs['scenario_id']
                # get the scenario for editing
                self.request.session['scenario'] = EMODBaseline.from_dw(pk=kwargs['scenario_id'])
        else:
            # Make sure there's a scenario in the session
            if 'scenario' not in self.request.session.keys():
                # create empty scenario
                self.request.session['scenario'] = EMODBaseline(
                    name='',
                    description='',
                    model=DimModel.objects.get(model='EMOD'),
                    user=DimUser.objects.get_or_create(username=self.request.user.username)[0]
                )

        if 'step' in kwargs.keys() and kwargs['step'] == 'climate':
            # 6230: redirect to Intervention Tool (if user clicked "Skip to Intervention Tool Button")
            # check to see if the user wants to jump over to the Intervention tool
            if 'jump_to_intervention_tool' in self.request.session.keys():
                my_scenario_id = self.request.session['scenario'].id
                # clear wizard storage
                self.storage.reset()
                del self.request.session['jump_to_intervention_tool']

                # redirect to Intervention Tool
                return redirect("ts_intervention_tool_step", scenario_id=my_scenario_id)


        self.request.session['scenario'].save()

        return super(BaselineWizardView, self).dispatch(request, *args, **kwargs)

    def render_done(self, form, **kwargs):
        """ Override the wizard's default render_done
        This method gets called when all forms passed. The method should also
        re-validate all steps to prevent manipulation. If any form don't
        validate, `render_revalidation_failure` should get called.
        If everything is fine call `done`.
        """
        final_form_list = []
        # walk through the form list and try to validate the data again.
        for form_key in self.get_form_list():
            form_obj = self.get_form(step=form_key,
                                     data=self.storage.get_step_data(form_key),
                                     files=self.storage.get_step_files(form_key))
            if not form_obj.is_valid():
                return self.render_revalidation_failure(form_key, form_obj, **kwargs)
            final_form_list.append(form_obj)

        # add in our own checks, fail validation here, so wizard isn't reset if we need to go back
        if not self.request.session['scenario'].has_required_files:
            my_missing = self.request.session['scenario'].get_missing_files()
            if len(my_missing) == 0:
                my_missing = ""
            else:
                my_missing = "Missing files: " + str(my_missing)

            set_notification('alert-error', '<strong>Error!</strong> This simulation is incomplete. ' + my_missing
                                            + ' Please go back and complete before approving.',
                             self.request.session)

            form_key = 'review'
            form_obj = self.get_form(step=form_key,
                                     data=self.storage.get_step_data(form_key),
                                     files=self.storage.get_step_files(form_key))
            return self.render_revalidation_failure(form_key, form_obj, **kwargs)

        # render the done view and reset the wizard before returning the
        # response. This is needed to prevent from rendering done with the
        # same data twice.
        done_response = self.done(final_form_list, **kwargs)
        self.storage.reset()
        return done_response

    def done(self, form_list, **kwargs):
        """A method that processes all the form data at the end of BaselineWizard

        Process then Save collected data from multiple forms into one DB table (Baseline)
        """

        # check to make sure at least one run has been done

        self.request.session['scenario'].is_approved = True
        my_id, completed = self.request.session['scenario'].save()

        if my_id == self.request.session['scenario'].id:
            # reset session variables
            del self.request.session['scenario']
            del self.request.session['scenario_config']
            set_notification('alert-success', '<strong>Success!</strong> Successfully saved.', self.request.session)

        return redirect("ts_emod_scenario_browse")

    def get_context_data(self, form, **kwargs):
        """Extension of the get_context_data method of the NamedUrlSessionWizardView.

        Select/process data based on which step of the Form Wizard it's called for.

        - Date: passes existing start_date, end_date values or nothing then template will use min and max.
        - Preview gets all wizard step data gathered so far.
        """
        context = super(BaselineWizardView, self).get_context_data(form=form, **kwargs)

        # All steps:
        if 'edit_scenario' in self.storage.extra_data:
            # if we're in edit mode, let templates know ("Start Over" vs "Cancel Edit" button)
            context['edit_scenario'] = self.storage.extra_data['edit_scenario']

        ######### Start code for specific steps #########

        if self.steps.current == 'location':
            the_request = self.request
            adapter = EMOD_Adapter(self.request.user.username)
            templates = adapter.fetch_template_list()  # get for description

            for key in templates.keys():
                if 'edit_scenario' in self.storage.extra_data \
                        and 'scenario' in self.request.session.keys() \
                        and self.request.session['scenario'].template is not None \
                        and self.request.session['scenario'].template.id is not None \
                        and self.request.session['scenario'].template.id == key:
                    # set the checked option based on the scenario being edited
                    templates[key]['checked'] = 1

                elif 'location' in self.storage.data['step_data'].keys()\
                    and 'location-template_id' in self.storage.data['step_data'][u'location'].keys()\
                    and unicode(key) == \
                        self.storage.data['step_data'][u'location'][u'location-template_id'][0]:
                    # set checked option based on wizard value already saved
                    templates[key]['checked'] = 1

            # For now: limit list to Solomon and Kenya templates
            templates_a = {}
            templates_b = {}
            templates_c = {}
            templates_d = {}
            templates_e = {}

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
            context['template_count'] = template_count
            context['current_start'] = pager_offset * pager_size + 1
            context['current_stop'] = min(template_count, pager_offset * pager_size + pager_size)
            return context

        if self.steps.current == 'climate':
            my_template = DimTemplate.objects.get(id=self.storage.extra_data['template_id'])
            context['template'] = my_template
            # set up the context to include the files (if any) attached to the scenario
            my_types = [
                'air binary',
                #'air json',
                'humidity binary',
                #'humidity json',
                #'land_temp binary',
                #'land_temp json',
                'rainfall binary']
                #'rainfall json']

            # get scenario files: types/names
            context['climate_files'] = {}
            for my_file in self.request.session['scenario'].get_files():
                # my_file[0] id
                # my_file[1] name
                # my_file[2] type
                if my_file[2] in my_types:
                    context['climate_files'].update({my_file[2].split(' ')[0]: my_file[1]})
            context['climate_files'] = sorted(context['climate_files'].iteritems())
            context['scenario_id'] = self.request.session['scenario'].id

            my_template = DimTemplate.objects.get(id=self.storage.extra_data['template_id'])
            context['template'] = my_template

        if self.steps.current == 'demographic':
            my_template = DimTemplate.objects.get(id=self.storage.extra_data['template_id'])
            context['template'] = my_template

        if self.steps.current == 'species':
            ###
            # Get list of species user can base NEW species creation on (drop-down menu)
            # and to use for adding to a simulation

            # get from template
            try:
                context['species_templates'] = \
                    self.storage.extra_data['scenario_template_config']['parameters']['Vector_Species_Params']
            except KeyError:
                pass

            ###
            # Modify the above list to make the "select from" sources
            species_list = []
            try:
                # turn into objects
                for key, value in context['species_templates'].items():
                    json_string = '{"' + key + '":' + json.dumps(value) + "}"
                    species_list.append(Species(name=key, is_template=1, is_public=0, json=json_string,
                                                created_by=self.request.user))
            except KeyError:
                pass

            # Add in public and user's own custom species objects from DB
            for species in Species.objects.filter(Q(is_public=1) | Q(created_by=self.request.user)):
                species_list.append(species)

            #  This serves as the "from template", "user's custom" and "public" species available
            context['species_list'] = species_list

            ###
            # Populate the already chosen list

            # # Get Baseline or Template ID for passing to SpeciesCreate View
            # #  because wizard storage won't be available in SpeciesCreate View
            my_scenario_id = self.storage.extra_data.get('scenario_id')

            my_species = []
            try:
                my_species.extend(self.request.session['scenario_config']['parameters']['Vector_Species_Names'])
            except (KeyError, TypeError):
                pass

            my_species = sorted(set(my_species))

            context['species_chosen'] = {u'species-species': json.dumps(my_species),
                                         'scenario_id': my_scenario_id,
                                         u'orig_json_obj': ConfigData.objects.filter(
                                         type='JSONConfig', name='default_emod_vector')[0].json}

            context['species_chosen_values'] = \
                json.dumps(self.request.session['scenario_config']['parameters']['Vector_Species_Params'])

        if self.steps.current == 'parasite' or self.steps.current == "vector":
            step_name = self.steps.current
            # build titles for template from name, misc
            my_object = ConfigData.objects.filter(type='JSONConfig', name=step_name)[0]
            context['step_title'] = step_name.title() + " " + my_object.misc.split(":")[1].title()
            context['description'] = my_object.description

            # if the user has not already been through this step
            #  populate the form with the template values.
            if not self.storage.get_step_data(step_name):
                try:
                    context['template_values'] = self.request.session['scenario_config']['parameters']
                except KeyError:
                    pass

        if self.steps.current == 'run':
            form.fields['name'].initial = 'Test Run ' + str(datetime.datetime.now())

        if self.steps.current == 'review':
            # get list of runs for this scenario
            adapter = EMOD_Adapter(self.request.user.username)

            run_list = DimRun.objects.filter(baseline_key=self.request.session['scenario'].id)

            if len(run_list) > 0:
                # sort descending by id (for those old runs that all have the same old time_created
                run_list = sorted(run_list, key=lambda x: x.id, reverse=True)
                # sort descending by time_saved
                run_list = sorted(run_list, key=lambda x: x.time_created, reverse=True)

                # get most recent run, is it still running?
                my_run = run_list[0]

                # check to see if a run is currently running
                status = adapter.run_status(my_run.id)

                if status is None:
                    my_run.my_completed = None
                else:
                    my_run.my_completed = status[0]
                    my_run.my_failed = status[2]
                    if status[0] > 0:
                        context['scenario_has_results'] = 1  # this sets if any of the runs here has results
                    my_run.my_total = status[1]
                    my_run.my_percent_complete = float(status[0]) / float(status[1]) * 100
                    my_run.my_percent_failed = float(status[2]) / float(status[1]) * 100
                    my_run.errors = adapter.fetch_errors(my_run.id)

                # get the results for the last run(s) if it's finished
                context['my_run'] = my_run

                # #6329 - pass in scenario for display of info
                context['scenario'] = self.request.session['scenario']
                my_config = self.request.session['scenario'].get_file_by_type('config').content
                context['Simulation_Duration'] = ast.literal_eval(my_config)['parameters']['Simulation_Duration']

        if self.steps.current == 'run':
            # check for existing runs in this scenario
            if 'scenario' in self.request.session.keys():
                my_runs = DimRun.objects.filter(baseline_key=self.request.session['scenario'].id)
                if len(my_runs) > 0:
                    context['has_runs'] = len(my_runs)
                    # populate the step data so if the skip button is used,
                    # the wizard doesn't skip back to here upon wizard submission (skip isn't a submit, just goto_step)
                    self.storage.set_step_data('run', {u'baseline_wizard_view-current_step': [u'run']})

        return context

    def get_form(self, step=None, data=None, files=None):
        form = super(BaselineWizardView, self).get_form(step, data, files)

        if step is not None and data is not None:
            # get_form is called for validation by get_cleaned_data_for_step()
            return form

        if self.steps.current == "parasite" or self.steps.current == "vector":
            form.fields['json'].label = ''  # "Settings"

            step_name = self.steps.current

            # if we've been here before, there will be data in the step storage
            if self.storage.get_step_data(step_name):
                form.fields['json'].initial = self.storage.get_step_data(step_name)
            else:
                # get initial values from DB.
                try:
                    form.fields['json'].initial = ConfigData.objects.filter(type='JSONConfig', name=step_name)[0].json
                except KeyError:
                    form.fields['json'].label = 'No parameters found. Please contact System Administrator.'

        return form

    def process_step(self, form):
        """ Method to handle "after Next-click" processing of steps """

        # set the flag that determines when to save the config to the scenario
        change_config = 0
        # set the flag that determines when to save the scenario
        change_scenario = 0

        adapter = EMOD_Adapter(self.request.user.username)

        if self.steps.current == 'config':
            if self.request.session['scenario_config']['parameters']['Simulation_Duration'] != \
                    form.cleaned_data['Simulation_Duration']:
                self.request.session['scenario_config']['parameters']['Simulation_Duration'] = \
                    form.cleaned_data['Simulation_Duration']
                change_config = 1
            if self.request.session['scenario_config']['parameters']['Simulation_Type'] != \
                    form.cleaned_data['Simulation_Type']:
                self.request.session['scenario_config']['parameters']['Simulation_Type'] = \
                    form.cleaned_data['Simulation_Type']
                change_config = 1
            if self.request.session['scenario_config']['parameters']['Start_Time'] != form.cleaned_data['Start_Time']:
                self.request.session['scenario_config']['parameters']['Start_Time'] = form.cleaned_data['Start_Time']
                change_config = 1

            if self.request.session['scenario'].name != form.cleaned_data['name']:
                self.request.session['scenario'].name = form.cleaned_data['name']
                change_scenario = 1

            if self.request.session['scenario'].description != form.cleaned_data['description']:
                self.request.session['scenario'].description = form.cleaned_data['description']
                change_scenario = 1

            # Workaround for bug #5626 config file is not saved if user doesn't change Simulation Duration on
            # Step 2 of 9: Configure Simulation
            change_config = 1

            # 6230: redirect to Intervention Tool (if user clicked "Skip to Intervention Tool Button")
            # Set session variable here, so dispatch at beginning of next step knows to redirect (wizard won't allow
            #  redirect here to work.
            if 'jump_to_intervention_tool' in self.request.POST.keys():
                self.request.session['jump_to_intervention_tool'] = 1

        if self.steps.current == 'species':
            species_list = form.cleaned_data['species']
            # if the list NOT matches the old list, update it
            if species_list != self.request.session['scenario_config']['parameters']['Vector_Species_Names']:
                self.request.session['scenario_config']['parameters']['Vector_Species_Names'] = species_list
                change_config == 1

            # check also for changes in the Vector Parameters (vector list may be the same)
            my_json = dict(form.data)

            # Gather parameter sets for all species in names list.
            parameter_dict = {}
            for species in species_list:
                # add each Vector to Params list
                my_dict = {}
                for key in sorted(my_json.keys()):  # sorted so Habitat_Type/Required_Habitat_Factor order preserved
                    if str(species) + '__json_' in key:
                        if type(my_json[key]) == list:
                            my_value = my_json[key][0]
                        else:
                            my_value = my_json[key]
                        if type(my_value) not in (float, int):
                            try:
                                my_value = int(str(my_value))
                            except (ValueError, TypeError):
                                try:
                                    my_value = float(str(my_value))
                                except (ValueError, TypeError):
                                    pass

                        if 'Required_Habitat_Factor' in key.split('__json_')[1]:
                            if my_value == '':
                                continue
                            if 'Required_Habitat_Factor' in my_dict.keys():
                                my_dict['Required_Habitat_Factor'].append(my_value)
                            else:
                                my_dict.update({'Required_Habitat_Factor': [my_value]})
                        elif 'Habitat_Type' in key.split('__json_')[1]:
                            if 'Habitat_Type' in my_dict.keys():
                                my_dict['Habitat_Type'].append(my_value)
                            else:
                                my_dict.update({'Habitat_Type': [my_value]})
                        elif key.split('__json_')[1] != 'obj':
                            my_dict.update({key.split('__json_')[1]: my_value})
                parameter_dict.update({species: my_dict})
            if self.request.session['scenario_config']['parameters']['Vector_Species_Params'] != parameter_dict:
                self.request.session['scenario_config']['parameters']['Vector_Species_Params'] = parameter_dict
                change_config = 1

        if self.steps.current == 'parasite':
            my_fields = json.loads(form.cleaned_data['json'])
            for key in my_fields:
                my_value = my_fields[key]['value']
                if type(my_value) in (str, unicode):
                    try:
                        my_value = int(my_value)
                    except ValueError:
                        try:
                            my_value = float(my_value)
                        except ValueError:
                            pass

                if my_value != self.request.session['scenario_config']['parameters'][key]:
                    self.request.session['scenario_config']['parameters'][key] = my_value
                    change_config = 1

        if self.steps.current == 'scaling_factors':
            my_value = form.cleaned_data['x_Temporary_Larval_Habitat']
            if type(my_value) in (str, unicode):
                try:
                    my_value = int(my_value)
                except ValueError:
                    try:
                        my_value = float(my_value)
                    except ValueError:
                        pass
            if my_value != self.request.session['scenario_config']['parameters']['x_Temporary_Larval_Habitat']:
                self.request.session['scenario_config']['parameters']['x_Temporary_Larval_Habitat'] = my_value
                change_config = 1

        # populate new scenario with template data
        #  or with existing scenario data if this call is for Editing a scenario
        if (self.steps.current == 'location' and form.cleaned_data['template_id'])\
                and ('template_id' not in self.storage.extra_data.keys()
                     or self.storage.extra_data['template_id'] != form.cleaned_data['template_id']):
            # todo: some of this is either edit-mode or new-mode: sort out later (depending on availability of data)

            template_id = int(form.cleaned_data['template_id'])

            if 'template_id' in self.storage.extra_data \
                    and template_id != self.storage.extra_data['template_id']:
                pass  # location_change = 1
            else:
                # first time through wizard, not a location change
                # location_change = 0
                # save schema
                self.request.session['schema.json'] = ConfigData.objects.filter(type='schema',
                                                                                name='emod-v1.5-schema.txt')[0].json

                # Set name here with dummy name as adding a file will attempt to save the scenario,
                # which fails if name is null
                if self.request.session['scenario'].name is None:
                    self.request.session['scenario'].name = ''
                    self.request.session['scenario'].description = ''

                # check for campaign file...
                try:
                    # if it exists, do nothing
                    self.request.session['scenario'].get_file_by_type('campaign')
                except ObjectDoesNotExist:
                    # else: add in empty campaign file
                    self.request.session['scenario'].add_file_from_string('campaign',
                                                                          'campaign.json',
                                                                          str({"Events": []}),
                                                                          description=self.steps.current)

            my_template_obj = DimTemplate.objects.get(id=template_id)

            self.request.session['scenario'].model_version = my_template_obj.model_version
            self.request.session['scenario'].dimbaseline.model_version = my_template_obj.model_version
            self.request.session['scenario'].template_id = template_id
            self.request.session['scenario'].template = my_template_obj
            self.request.session['scenario'].save()

            location_id = my_template_obj.location_key_id

            self.request.session['scenario'].template_id = template_id
            self.request.session['scenario'].template = my_template_obj
            # needed for editing
            if self.request.session['scenario'].dimbaseline is not None:
                self.request.session['scenario'].dimbaseline.template = my_template_obj
                self.request.session['scenario'].dimbaseline.template_id = template_id
            change_scenario = 1

            # Populate the step data with the chosen location's data
            self.storage.extra_data.update({'template_id': template_id})

            # populate config to the session for multiple uses later
            template_config = ast.literal_eval(my_template_obj.get_file_content('config.json'))
            if 'edit_scenario' in self.storage.extra_data.keys() \
                    and 'config' not in self.request.session['scenario'].get_missing_files():
                # use scenario's config file
                try:
                    self.request.session['scenario_config'] = \
                        ast.literal_eval(self.request.session['scenario'].get_file_by_type('config').content)
                except AttributeError:
                    # if query set returned, use first file in "list"
                    file_list = self.request.session['scenario'].get_file_by_type('config')
                    self.request.session['scenario_config'] = \
                        ast.literal_eval(file_list[0].content)
            else:
                # use template's (or parent scenario's) config file
                self.request.session['scenario_config'] = copy.deepcopy(template_config)
            self.storage.extra_data.update({'scenario_template_config': template_config})

            change_config = 1

            #########################
            ### Add default files to scenario

            # todo: stop using template zips, when climate files are available elsewhere
            print my_template_obj.climate_url

            self.storage.extra_data.update({'location_zip_link': my_template_obj.climate_url})

            # Do we cache zip to temp dir first time, and always access them from there (if they exist)
            # FILE_UPLOAD_TEMP_DIR
            # setup work directory
            #my_directory = os.path.join(settings.MEDIA_ROOT, 'uploads/expert_emod/')
            #my_directory = os.path.join(FILE_UPLOAD_TEMP_DIR, 'ts_emod/')
            #if not os.path.exists(my_directory):
            #    os.makedirs(my_directory)

            #inStream = urllib2.urlopen('http://dl-vecnet.crc.nd.edu/downloads/wh246s153')
            #inStream = urllib2.urlopen('https://dl.vecnet.org/downloads/wh246s153')
            if 'location_zip_link' in self.storage.extra_data:
                if settings.DEBUG is True:
                    now = datetime.datetime.now()
                    print now, " DEBUG: getting zip file: ", self.storage.extra_data['location_zip_link']
                url = urlopen(self.storage.extra_data['location_zip_link'])
                zipfile = ZipFile(StringIO(url.read()))

                for zip_file_name in zipfile.namelist():
                    if settings.DEBUG is True:
                        now = datetime.datetime.now()
                        print now, " DEBUG: handling file: ", zip_file_name
                    my_file = zipfile.open(zip_file_name)
                    my_name = ntpath.basename(zip_file_name)

                    # determine which file type this is
                    # my_name contains 'demographics' ?  (use compiled, store both?) Honiara_demographics.static.compiled.json Honiara_demographics.json
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
                            self.request.session['scenario'].add_file_from_string(my_type, my_name,
                                                                                  my_file.read(),
                                                                                  description=self.steps.current)
                        else:
                            self.request.session['scenario'].add_file_from_string(my_type, my_name,
                                                                                  my_file.read(),
                                                                                  description=self.steps.current)
                        change_scenario = 1

                        # todo: fix to allow separate air and land temp files
                        # for now: use same files for air temp and land temp
                        if my_type in ('air binary', 'air json'):
                            my_type = my_type.replace('air', 'land_temp')
                            self.request.session['scenario'].add_file_from_string(my_type, my_name,
                                                                                  "no land temp file",
                                                                                  description=self.steps.current)
            ### END if zip file is none

            # could save here to free up memory from the object file storage
            # but it fails without a name
            #if change_scenario == 1:
            #    self.request.session['scenario'].save()
            ###  END Zip/Input File handling
            ######################

            # config step data:
            self.storage.set_step_data('config', {u'config-name': [self.request.session['scenario']._name],
                                                  u'config-description': [self.request.session['scenario'].description],
                                                  u'config-Start_Time': [self.request.session['scenario_config']['parameters']['Start_Time']],
                                                  u'config-Simulation_Duration':
                                                  [self.request.session['scenario_config']['parameters']['Simulation_Duration']],
                                                  u'config-Simulation_Type':
                                                  [self.request.session['scenario_config']['parameters']['Simulation_Type']],
                                                  })

            # climate step data:
            self.storage.set_step_data('climate', {u'climate-location': [location_id]})

            # demographic step data:
            self.storage.set_step_data('demographic', {u'demographic-location': [location_id]})

            # parasite
            for step_name in ["vector", "parasite"]:
                # get db config for the step
                my_json = ConfigData.objects.filter(type='JSONConfig', name=step_name)[0].json

                # wizard values based on config + template values
                my_wiz = {u'orig_json_obj': [my_json]}
                my_json = json.loads(my_json)
                for key in my_json.keys():
                    try:
                        # = scenario value OR template value
                        # change into wizard format step name + -json_ + key name
                        my_wiz.update({u'' + step_name + '-json_'
                                       + key: [u'' + str(self.request.session['scenario_config']['parameters'][key])]})
                    except KeyError:
                        pass

                # insert into wizard storage
                self.storage.set_step_data(step_name, my_wiz)

            # Scaling step data:
            self.storage.set_step_data('scaling_factors',
                                       {u'scaling_factors-x_Temporary_Larval_Habitat':
                                       [self.request.session['scenario_config']['parameters']['x_Temporary_Larval_Habitat']]})

        # save any changes made to the scenario config file
        if change_config == 1 and self.steps.current != 'location':
            self.request.session['scenario'].add_file_from_string('config', 'config.json',
                                                                  str(self.request.session['scenario_config']),
                                                                  description=self.steps.current)
            change_scenario = 1

        if change_scenario == 1 and self.steps.current != 'location':
            # don't save until config step (name and description will be populated there.

            try:
                my_id, completed = self.request.session['scenario'].save()
                set_notification('alert-success', 'The simulation was saved. ', self.request.session)
            except KeyError:
                set_notification('alert-error', 'Error: The simulation was not saved. ', self.request.session)

        ###########################
        ### Create a run with scenario settings
        #    - launch it
        #    - display status
        #  ??? Do we want to force/allow user to add name/description to these runs?
        #  ??? Cap duration for initial run? 5 years?
        if self.steps.current == 'run':
            # create a new run instance
            adapter = EMOD_Adapter(self.request.user.username)

            my_template = DimTemplate.objects.get(id=self.request.session['scenario'].template.id)

            my_start_date = \
                datetime.datetime.strptime(
                    my_template.climate_start_date,
                    '%Y-%m-%d').date() \
                + datetime.timedelta(days=self.request.session['scenario_config']['parameters']['Start_Time'])

            my_run = adapter.save_run(
                                      template_id=int(self.request.session['scenario'].template.id),
                                      start_date=my_start_date,
                                      duration=100,  # 1825, 5 years
                                      #=self.request.session['scenario_config']['parameters']['Simulation_Duration'],
                                      name=form.cleaned_data['name'],  # self.request.session['scenario'].name + ': Test Run '
                                      description='Run by New Simulation Wizard',
                                      location_ndx=my_template.location_key.id,
                                      timestep_interval=1,
                                      run_id=-1,  # run_id,
                                      as_object=True)

            my_run.scenario_key_id = self.request.session['scenario'].id
            my_run.save()

            if settings.DEBUG:
                print "DEBUG: line 890 BaselineWiz: run id: ", my_run.id

            # add in JCD for it for config file
            changes = []
            newdict = copy.deepcopy(self.request.session['scenario_config'])

            newdict['config.json/parameters'] = newdict.pop('parameters')
            changes.append(Change.node(name='config.json', node=[newdict], mode='-'))
            my_run.jcd = JCD.from_changes(changes)

            my_run.save()

            ### Launch the run

            # save launch info to extra data todo: this should eventually go into success block below
            self.storage.extra_data['last_launched_run'] = my_run.id

            # submit returns tuple (success, message)
            status = submit(my_run, user=self.request.user, manifest=True, reps_per_exec=1)

            try:
                if status[0] is True:
                    set_notification('alert-success', '<strong>Success!</strong> Test Run launched.',
                                     self.request.session)
                else:
                    set_notification('alert-error', '<strong>Error!</strong> ' + status[1], self.request.session)
            except TypeError:
                pass

        return self.get_form_step_data(form)
    ### END process_step

    def post_UNUSED(self, *args, **kwargs):
        """ Override post method
            - save form values when wizard_goto_step is triggered
             - such as "Previous Step" button
             - or navigation buttons
        """
        wizard_goto_step = self.request.POST.get('wizard_goto_step', None)

        if wizard_goto_step and wizard_goto_step in self.get_form_list():
            form = self.get_form(data=self.request.POST, files=self.request.FILES)
            if form.is_valid():
                self.storage.set_step_data(self.steps.current,
                                           self.process_step(form))
                self.storage.set_step_files(self.steps.current,
                                            self.process_step_files(form))

            self.storage.current_step = wizard_goto_step
            return redirect(self.get_step_url(wizard_goto_step))
        return super(BaselineWizardView, self).post(*args, **kwargs)

## An instance of BaselineWizardView
#
# Use step names/Forms tuple defined in forms file.
baseline_wizard = BaselineWizardView.as_view(named_baseline_forms,
                                             url_name='ts_scenario_step', done_step_name='complete')


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
