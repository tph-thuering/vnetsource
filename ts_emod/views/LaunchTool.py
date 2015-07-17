########################################################################################################################
# VECNet CI - Prototype
# Date: 4/23/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

from change_doc import Change, JCD
from data_services.adapters.EMOD import EMOD_Adapter
from data_services.data_api import EMODBaseline
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.formtools.wizard.views import NamedUrlSessionWizardView
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from job_services.dispatcher import submit
from lib.templatetags.base_extras import set_notification
from ts_repr.models import RepresentativeScenario
from ts_emod.forms import named_launch_tool_forms

import ast
import copy
import datetime


## An extension of django.contrib.formtools.wizard.views.NamedUrlSessionWizardView
#
# Inputs: scenario id in the url
# Outputs: send signal to cluster service to run the scenario's newly created run


class LaunchTool(NamedUrlSessionWizardView):
    template_name = 'ts_emod/launch_tool.html'

    @method_decorator(login_required)
    ## Override method to create a Run instance for the form at dispatch time
    def dispatch(self, request, *args, **kwargs):
        #self.instance = Run()
        return super(LaunchTool, self).dispatch(request, *args, **kwargs)

    ## Override method to create a Run instance for the form, for each step.
    #def get_form_instance(self, step):
    #    if self.instance is None:
    #        self.instance = Run()
    #    return self.instance

    ## Extension of the get_context_data method of the NamedUrlSessionWizardView.
    #
    # Handle the url-passed run id
    def get_context_data(self, form, **kwargs):
        context = super(LaunchTool, self).get_context_data(form, **kwargs)

        try:
            context['nav_button'] = self.request.session['emod_nav_button']
        except KeyError:
            pass

        # We need either a run id or scenario id (both really)
        if 'run_id' in kwargs:
            run_id = kwargs['run_id']
            if run_id > 0:
                self.storage.extra_data['emod_launch_run_id'] = run_id
                context['run_named'] = 1
                # get the run's name, to prepopulate the name field
                adapter = EMOD_Adapter(self.request.user.username)
                my_run_id = int(self.storage.extra_data['emod_launch_run_id'])
                my_run = adapter.fetch_runs(scenario_id=-1, run_id=int(my_run_id))
                context['form'].fields['name'].initial = my_run.name
                # save for checking for changes in done method
                self.storage.extra_data['old_run_name'] = my_run.name
        #else:
        # get the specified scenario - error if none specified
        try:
            if 'scenario_id' in kwargs:
                self.storage.extra_data['scenario_id'] = kwargs['scenario_id']
            elif 'scenario_id' not in self.storage.extra_data:
                self.storage.extra_data['error_invalid_id'] = 1
                Exception()
        except KeyError:
            #If there was no scenario id in the url or storage, this wizard is useless... redirect somewhere else
            set_notification('alert-error', 'Error Launching Simulation: Unknown/Invalid run provided. ' +
                                            'Please select a simulation below to launch.', self.request.session)
        return context

    ## A method that provides end-of-LaunchTool processing
    #
    # Create a run (and JCD) from scenario (campaign.json, config.json, etc.)
    # and launch it
    def done(self, form_list, **kwargs):
        if 'error_invalid_id' in self.storage.extra_data:
            self.storage.reset()
            set_notification('alert-error', 'Error Launching Simulation: Unknown/Invalid run provided. ' +
                                            'Please select a simulation below to launch.', self.request.session)
            return redirect("ts_emod_scenario_browse")

        if 'scenario_id' in self.storage.extra_data:
            scenario_id = int(self.storage.extra_data['scenario_id'])
        else:
            Exception()

        adapter = EMOD_Adapter(self.request.user.username)

        if 'emod_launch_run_id' in self.storage.extra_data:
            my_run_id = int(self.storage.extra_data['emod_launch_run_id'])
            my_run = adapter.fetch_runs(scenario_id=-1, run_id=int(my_run_id))
            # check for name changes from user
            start_data = self.get_cleaned_data_for_step('start')
            if self.storage.extra_data['old_run_name'] != start_data['name']:
                my_run.name = start_data['name']
                my_run.save()
        else:
            # get the scenario
            self.storage.extra_data['scenario'] = EMODBaseline.from_dw(pk=scenario_id)
            my_config = ast.literal_eval(self.storage.extra_data['scenario'].get_file_by_type('config').content)

            try:
                my_campaign = ast.literal_eval(self.storage.extra_data['scenario'].get_file_by_type('campaign').content)
            except AttributeError:
                # if file list was returned, use last file
                file_list = self.request.session['scenario'].get_file_by_type('campaign')
                my_campaign = ast.literal_eval(file_list[0].content)

            my_campaign_length = len(my_campaign['Events'])

            ###
            # create a new run instance

            if my_campaign_length > 0:
                with_interventions = "with interventions "
            else:
                with_interventions = ""

            my_simulation_duration = my_config['parameters']['Simulation_Duration']

            ## Set the run start_date based on location and config's start_time
            my_start_date = \
                datetime.datetime.strptime(
                    self.storage.extra_data['scenario'].template.climate_start_date,
                    '%Y-%m-%d').date() \
                + datetime.timedelta(days=my_config['parameters']['Start_Time'])

            # Initialize the run
            my_run = adapter.save_run(scenario_id=scenario_id,
                                      template_id=int(self.storage.extra_data['scenario'].template.id),
                                      start_date=my_start_date,
                                      duration=my_simulation_duration,
                                      name=self.get_cleaned_data_for_step('start')['name'],
                                      description='Launch Tool: ' + self.storage.extra_data['scenario'].name
                                                  + ': Run ' + with_interventions + str(datetime.datetime.now()),
                                      location_ndx=self.storage.extra_data['scenario'].template.location_key.id,
                                      timestep_interval=1,
                                      run_id=-1,
                                      as_object=True)

            my_run.baseline_key_id = scenario_id
            my_run.save()

            if settings.DEBUG:
                print "DEBUG: LaunchTool: run id: ", my_run.id

            # add in JCD for config file
            changes = []
            newdict = copy.deepcopy(my_config)

            newdict['config.json/parameters'] = newdict.pop('parameters')
            changes.append(Change.node(name='config.json', node=[newdict], mode='-'))

            # add in JCD for campaign file
            if my_campaign_length > 0:
                newdict = copy.deepcopy(my_campaign)
                newdict['campaign.json/Use_Defaults'] = newdict.pop('Use_Defaults')
                newdict['campaign.json/Events'] = newdict.pop('Events')
                changes.append(Change.node(name='campaign.json', node=[newdict], mode='-'))

            my_run.jcd = JCD.from_changes(changes)
            my_run.save()

        ### Launch the run

        # 5853 - hard-code to 1 for now
        #reps_per_exec = int(self.get_cleaned_data_for_step('start')['reps_per_exec'])
        reps_per_exec = 1

        # If this is a representative based scenario, then set it to non-editable
        representative_scenario = RepresentativeScenario.objects.filter(emod_scenario_id=scenario_id)
        if representative_scenario:
            representative_scenario[0].is_editable = False
            representative_scenario[0].save()

        # submit returns tuple (success, message)
        try:
            status = submit(my_run, user=self.request.user, manifest=True, reps_per_exec=reps_per_exec)

            set_notification('alert-success', '<strong>Success!</strong> Run launched.',
                             self.request.session)
        except (RuntimeError, TypeError, AssertionError), e:
            set_notification('alert-error', '<strong>Error!</strong> ' + str(e.message), self.request.session)

        # clear out saved form data.
        self.storage.reset()

        return redirect("ts_emod_scenario_details", scenario_id=scenario_id)

    # END done

    ## Extension of the get method of the NamedUrlSessionWizardView.
    # In event of error, clear wizard storage and redirect back to browse view
    def get(self, request, *args, **kwargs):
        response = super(LaunchTool, self).get(request, *args, **kwargs)
        if 'error_invalid_id' in self.storage.extra_data:
            self.storage.reset()
            return redirect("ts_emod_scenario_browse")
        return response

## An instance of LaunchTool
#
# Use step names/Forms tuple defined above.
launch_tool_view = LaunchTool.as_view(named_launch_tool_forms,
                                      url_name='ts_emod_launch_tool', done_step_name='complete')
