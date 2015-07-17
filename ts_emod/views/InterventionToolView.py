########################################################################################################################
# VECNet CI - Prototype
# Date: 04/16/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app
from django.http import HttpResponse
from data_services.adapters.EMOD import EMOD_Adapter
from data_services.data_api import EMODBaseline
from data_services.models import DimTemplate, DimUser
from django.contrib.formtools.wizard.storage import get_storage
from django.contrib.formtools.wizard.views import NamedUrlSessionWizardView
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
import ast
import re
import json
from lib.templatetags.base_extras import set_notification

# Imports that are internal to the ts_emod app

from ts_emod.models import Intervention, ConfigData
from ts_emod.forms import InterventionCreateForm, BaselineInterventionForm


class InterventionToolView(NamedUrlSessionWizardView):
    """An extension of django.contrib.formtools.wizard.views.NamedUrlSessionWizardView

    For creating an EMOD Scenario through multiple wizard steps.
    Inputs: config settings from DB rows + user input.
    Outputs: Save intervention to DB
    """

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """ The method that accepts a request argument plus arguments, and returns an HTTP response.

        - Verify that the user owns the selected scenario
        - if not, go to selection page with error message
        """
        # add the storage engine to the current wizard view instance here so we can act on storage here
        self.prefix = self.get_prefix(*args, **kwargs)
        self.storage = get_storage(self.storage_name, self.prefix, request, getattr(self, 'file_storage', None))

        # Maybe not need to set a flag to make this block work - if first time, we NEED an id
        #   - if revisit, should do nothing here but continue (example: user reloads page)
        #if not kwargs['scenario_id']:
        #    set_notification('alert-error',
        #                     'Please select a simulation to work in.',
        #                     request.session)
        #    return redirect("ts_emod_scenario_browse")

        if 'scenario_id' in kwargs.keys() and kwargs['scenario_id'] > 0:
            #todo: check for intervention_tool in self.storage.extra_data.keys() ??

            # First hit in Edit mode - populate the steps with initial defaults
            try:
                self.storage.reset()
                self.storage.extra_data['intervention_tool'] = kwargs['scenario_id']
            except AttributeError:
                pass
            # get the scenario for editing
            self.request.session['scenario'] = EMODBaseline.from_dw(pk=kwargs['scenario_id'])

        if str(self.request.session['scenario'].user) == \
                str(DimUser.objects.get_or_create(username=self.request.user.username)[0]):
            return super(InterventionToolView, self).dispatch(request, *args, **kwargs)
        else:
            set_notification('alert-error',
                             'You cannot modify simulations unless you own them.  '
                             'Please select a simulation to work in.',
                             request.session)
            return redirect("ts_emod_scenario_browse")

    def get_template_names(self):
        """ A method to provide the step name/template dictionary """
        TEMPLATES = {"intervention": "ts_emod/intervention_tool.html"}
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        """A method that processes all the form data at the end of Intervention Tool

        Process, Save collected data into scenario
        """
        # TODO: still need to handle saving after removing all interventions
        try:
            my_campaign = self.storage.extra_data['my_campaign']
            my_length = len(my_campaign['Events'])
            my_config = ast.literal_eval(self.request.session['scenario'].get_file_by_type('config').content)
        except KeyError:
            my_length = 0

        if my_length > 0:
            # enable in config
            if my_config['parameters']['Enable_Interventions'] == 0:
                my_config['parameters']['Enable_Interventions'] = 1

                self.request.session['scenario'].add_file_from_string('config', 'config.json',
                                                                      str(my_config),
                                                                      description="Modified by Intervention Tool")
            # add in campaign file
            self.request.session['scenario'].add_file_from_string('campaign', 'campaign.json',
                                                                  str(my_campaign),
                                                                  description="Added by Intervention Tool")

        set_notification('alert-success', '<strong>Success!</strong> The intervention(s) have been saved to ' +
                         self.request.session['scenario'].name + '.', self.request.session)

        # check if user wants to launch, or just save
        if 'launch' in self.storage.data['step_data']['intervention'] \
           and str(self.storage.data['step_data']['intervention']['launch'][0]) == '1':
            launch_flag = True
        else:
            launch_flag = False

        # save this for redirect use
        my_scenario_id = self.request.session['scenario'].id

        # clear out saved form data.
        self.storage.reset()
        if 'scenario' in self.request.session.keys():
            del self.request.session['scenario']

        if launch_flag:
            return redirect("ts_emod_launch_tool", step='start', scenario_id=str(my_scenario_id))
        else:
            return redirect("ts_emod_scenario_details", scenario_id=str(my_scenario_id))

    def get_context_data(self, form, **kwargs):
        """Extension of the get_context_data method of the NamedUrlSessionWizardView.

        Select/process data based on which step of the Form Wizard it's called for.

        - Put into context the available interventions (from DB)
        - And if any, previously selected interventions (from scenario's campaign file or wizard storage)
        - todo: Dates: passes existing start_date, end_date values or nothing then template will use min and max.
        """
        context = super(InterventionToolView, self).get_context_data(form=form, **kwargs)

        if self.steps.current == 'intervention':
            # get list of interventions on shelf (to choose from)
            intervention_list = []

            # list of interventions in template

            # populate campaign to the session for multiple uses later
            my_template = DimTemplate.objects.get(id=self.request.session['scenario'].template.id)
            my_campaign = ast.literal_eval(my_template.get_file_content('campaign.json'))

            template_counter = 0
            for my_intervention in my_campaign['Events']:
                my_json = json.dumps(my_intervention['Event_Coordinator_Config']['Intervention_Config'])

                interv_obj = Intervention(id="template_" + str(template_counter), json=my_json,
                                          name=my_intervention['Event_Coordinator_Config']['Intervention_Config'][
                                              'class'], description='An example intervention')
                intervention_list.append(interv_obj)
                template_counter += 1

            context['intervention_list'] = intervention_list

            if self.request.user.is_authenticated():
                # list of available interventions from local DB (public OR created by user)
                for item in list(Intervention.objects.filter(Q(is_public=1) | Q(created_by=self.request.user))):
                    intervention_list.append(item)
            else:
                set_notification('alert-error',
                                 '<strong>Error!</strong> You are not logged in. Continuing in development mode '
                                 '(this will be removed soon, then you would be redirected to a login screen).',
                                 self.request.session)
                # list of available interventions from local DB (public OR created by user)
                for item in list(Intervention.objects.filter(Q(is_public=1))):  # | Q(created_by=self.request.user))):
                    intervention_list.append(item)

            # get uploaded campaign file - move from session to wizard storage
            if 'uploaded_file_campaign' in self.request.session.keys():
                my_campaign = self.request.session['uploaded_file_campaign']

                for counter, event in enumerate(my_campaign['Events']):
                    event['Event_Coordinator_Config']['Intervention_Config']['my_name'] = \
                        event['Event_Coordinator_Config']['Intervention_Config']['class'] + "_" + str(counter + 1) + \
                        "_from_file_" + self.request.session['uploaded_file_campaign_name'].replace(" ", "")

                self.storage.extra_data['my_campaign'] = my_campaign

                context['my_campaign'] = json.dumps(my_campaign)

                del self.request.session['uploaded_file_campaign']
                del self.request.session['uploaded_file_campaign_name']

            else:
                # get list of user-selected interventions (already placed in shopping cart)
                try:
                    context['my_campaign'] = json.dumps(ast.literal_eval(self.request.session['scenario'].get_file_by_type('campaign').content))
                except AttributeError:
                    # if file list was returned, use last file
                    file_list = self.request.session['scenario'].get_file_by_type('campaign')
                    context['my_campaign'] = json.dumps(ast.literal_eval(file_list[0].content))

                if 'Events' not in ast.literal_eval(self.request.session['scenario'].get_file_by_type('campaign').content).keys():
                    context['my_campaign'] = {"Events": []}

            # get date data to determine the max allowable start_date for interventions.
            #
            # get the config
            #
            my_config = ast.literal_eval(self.request.session['scenario'].get_file_by_type('config').content)
            try:
                context.update({'start_day_max': my_config['parameters']['Simulation_Duration']})
                context.update({'start_day_min': my_config['parameters']['Start_Time']})
            except TypeError:
                # Based on EMOD documentation
                context.update({'start_day_max': 2147480000})
                context.update({'start_day_min': 0})

            # NEW Interventions page: list of interventions available to create from
            new_intervention_list = []
            for interv in ConfigData.objects.filter(type='JSONConfig_intervention'):
                new_intervention_list.append(interv.name)

            context['new_intervention_list'] = json.dumps(new_intervention_list)

            new_intervention_form = InterventionCreateForm()

            new_intervention_form.fields['json'].label = ''

            # get initial values from DB.
            try:
                new_intervention_form.fields['json'].initial = \
                    ConfigData.objects.filter(type='JSONConfig_intervention',
                                              name='Please select an intervention type')[0].json
            except IndexError:
                new_intervention_form.fields['json'].label = 'No parameters found. Please contact System Administrator.'

            context['new_intervention_form'] = new_intervention_form
            context['scenario'] = self.request.session['scenario']  # #6328 - add this to display sim id/name
            context['intervention_names_list'] = json.dumps([intervention.name for intervention in intervention_list])

        return context

    def process_step(self, form):
        """ Method to handle "after Next-click" processing of steps """
        adapter = EMOD_Adapter(self.request.user.username)

        if self.steps.current == 'intervention':
            # temp filling for settings
            settings_data = []
            my_config = ""

            my_json = dict(form.data)

            # make sure number types are saved as numbers
            for my_field in my_json.keys():
                if type(my_json[my_field]) in (str, unicode):
                    try:
                        my_json[my_field][0] = int(my_json[my_field][0])
                    except ValueError:
                        try:
                            my_json[my_field][0] = float(my_json[my_field][0])
                        except ValueError:
                            pass
                elif type(my_json[my_field]) == list:
                    for index, my_list_field in enumerate(my_json[my_field]):
                        try:
                            my_json[my_field][index] = int(str(my_json[my_field][index]))
                        except ValueError:
                            try:
                                my_json[my_field][index] = float(str(my_json[my_field][index]))
                            except ValueError:
                                pass

            try:
                enumerate(my_json['intervention-interventions'])
            except (KeyError, ValueError):
                my_json = dict({"intervention-interventions": ["EMPTY:EMPTY"]})

            my_campaign = json.loads(
                '{ "Events": [ { "Event_Coordinator_Config": { "Intervention_Config": {}, "class": '
                '"StandardInterventionDistributionEventCoordinator" }, "Nodeset_Config": { "class": '
                '"NodeSetAll" }, "Start_Day": 0, "class": "CampaignEvent" } ]}')

            i = 0
            for idx, value in enumerate(my_json['intervention-interventions']):
                # 'intervention-interventions': [u'1:Simple Bednets', u'2:Insect killing Fence']
                #  - id : name
                # Skip EMPTY placeholder intervention
                if 'EMPTY' in value.split(':')[0]:
                    continue

                my_interv_id = value.split(':')[0]

                if 'upload_' in my_interv_id:
                    # make sure interventions are enabled in config
                    if my_config['parameters']['Enable_Interventions'] == 0:
                        settings_data.append('config.json/parameters/Enable_Interventions=1')
                    self.storage.extra_data.update({'my_campaign': self.request.session['uploaded_file_campaign']})
                else:
                    my_interv_config = {}
                    for key in form.data.keys():
                        if re.match(r'^' + my_interv_id + '__json_', key):
                            my_interv_config.update({key.replace(my_interv_id + '__json_', ''): form.data[key]})

                    if type(my_interv_config) != dict:
                        my_interv_config = json.loads(my_interv_config)

                    try:
                        my_campaign['Events'][i]['Event_Coordinator_Config'][
                            'Intervention_Config'] = my_interv_config  # json.loads(my_interv_config)
                    except:
                        # use ast.literal_eval to prevent copy from referring back original in JSON
                        # ToDo: use copy.deepcopy() instead
                        my_campaign['Events'].append(ast.literal_eval(str(my_campaign['Events'][i - 1].copy())))
                        my_campaign['Events'][i]['Event_Coordinator_Config']['Intervention_Config'] = my_interv_config

                    my_campaign['Events'][i]['Event_Coordinator_Config']['Intervention_Config']['my_name'] = \
                        my_json['intervention-interventions'][idx].split(":")[1]
                    my_campaign['Events'][i]['Event_Coordinator_Config']['Demographic_Coverage'] = float(
                        my_json['intervention-demographic_coverage'][idx])
                    my_campaign['Events'][i]['Event_Coordinator_Config']['Number_Repetitions'] = int(
                        my_json['intervention-num_repetitions'][idx])
                    my_campaign['Events'][i]['Event_Coordinator_Config']['Timesteps_Between_Repetitions'] = int(
                        my_json['intervention-Timesteps_Between_Repetitions'][idx])
                    my_campaign['Events'][i]['Event_Coordinator_Config']['Number_Distributions'] = int(
                        my_json['intervention-Number_Distributions'][idx])
                    my_campaign['Events'][i]['Start_Day'] = float(my_json['intervention-start_day'][idx])
                    my_campaign['Events'][i]['Event_Coordinator_Config']['Travel_Linked '] = 0  # required by EMOD?
                    i += 1

            if i > 0:
                self.storage.extra_data.update({
                    'my_campaign': json.loads(
                        '{"Events": ' + json.dumps(my_campaign['Events']) + ', "Use_Defaults": 1 }')})
                settings_data.append('config.json/parameters/Enable_Interventions=1')
            else:
                # clear out as none were selected (no need to fill in empty Events here, done will handle that)
                self.storage.extra_data.update({'my_campaign': {}})

        return self.get_form_step_data(form)

named_forms = (
    ('intervention', BaselineInterventionForm),
)


def saveIntervention(request, Intervention_id=None):
    if request.method == 'POST':
        # check to see where to redirect to (who called this)
        if request.POST.get("calling_page") == 'ts_intervention_tool_step':
            return_to = intervention_tool
        # else:
        #     return_to = scenario_wizard

        # get keys from orig_json_obj
        settings_data = []

        my_json_dict = {}
        for key in request.POST.keys():  # request.POST.get("orig_json_obj").keys:
            if re.search(r"(^json_)", key):
                settings_data.append('config.json/parameters/' + str(key).replace('json_', '') + '='
                                     + str(request.POST.get(key)))

                my_dict_key = str(key).replace('json_', '')
                my_json_dict[my_dict_key] = can_be_number(request.POST.get(key))

        #3633 - add class field containing user-supplied name
        my_json_dict['my_name'] = request.POST.get('my_name').replace(' ', '_')

        my_json = json.dumps(my_json_dict)

        intervention = Intervention(name=request.POST.get("my_name").replace(' ', '_'),
                                    description=request.POST.get("my_description"),
                                    orig_json_obj=request.POST.get("orig_json_obj"),
                                    json=my_json,
                                    settings=settings_data,
                                    created_by=request.user,
                                    is_public=0)
        intervention.save()

    if intervention.id is None:
        return redirect(return_to, step="intervention")
    else:
        request.session['intervention_id'] = str(intervention.id)
        if return_to == intervention_tool:
            kwargs = {"scenario_id": str(request.session['scenario'].id)}
        else:
            kwargs = {"intervention_id": str(intervention.id)}
        return redirect(return_to, step="intervention", **kwargs)


## Function to delete Intervention DB Objects
#
def deleteIntervention(request, intervention_id):
    try:
        Intervention_to_delete = Intervention.objects.get(id=intervention_id, created_by=request.user.id)
        Intervention_to_delete.delete()
        set_notification('alert-success', '<strong>Success!</strong> You have successfully deleted the Intervention.',
                         request.session)
    except:
        print 'Error deleting Intervention with id: %s' % intervention_id
        set_notification('alert-error', '<strong>ERROR:</strong> There was a problem that prevented '
                                        'the deletion of the Intervention.', request.session)
    # return redirect(scenario_wizard, step="intervention")


def getFormIntervention(request, form_name=None):
    if form_name is not None:
        form_name = form_name.lstrip(' ')

    new_intervention_form = InterventionCreateForm()
    new_intervention_form.fields['json'].label = ''

    # get initial values from DB.
    try:
        new_intervention_form.fields['json'].initial = ConfigData.objects.get(type='JSONConfig_intervention',
                                                                              name=form_name).json
    except:
        new_intervention_form.fields['json'].label = 'No parameters found. Please contact System Administrator.'

    #return HttpResponse(new_intervention_form.as_grid_div())
    return HttpResponse(new_intervention_form.as_p())


def can_be_number(s):
    """
    # 3669
    Converts a string to an integer or a float.

    Returns initial value if the string cannot be converted.
    """
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s

## An instance of InterventionToolView
#
# Use step names/Forms tuple defined in forms file.
intervention_tool = InterventionToolView.as_view(named_forms,
                                             url_name='ts_intervention_tool_step', done_step_name='complete')