########################################################################################################################
# VECNet CI - Prototype
# Date: 05/05/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app
from change_doc import Change, JCD
from data_services.adapters.EMOD import EMOD_Adapter
from data_services.data_api import EMODBaseline
from data_services.models import DimRun, DimTemplate, DimUser
from django.contrib.formtools.wizard.storage import get_storage
from django.contrib.formtools.wizard.views import NamedUrlSessionWizardView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
import ast
import copy
import datetime
import json
from lib.templatetags.base_extras import set_notification

# Imports that are internal to the ts_emod app

from ts_emod.forms import named_sweep_tool_forms
from ts_emod.models import ConfigData


class SweepToolView(NamedUrlSessionWizardView):
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

	    # ToDo: make this importable (used in several views)
        # add the storage engine to the current wizard view instance here so we can act on storage here
        self.prefix = self.get_prefix(*args, **kwargs)
        self.storage = get_storage(self.storage_name, self.prefix, request, getattr(self, 'file_storage', None))

        if 'scenario_id' in kwargs.keys() and kwargs['scenario_id'] > 0:
            # get the scenario for editing
            self.request.session['scenario'] = EMODBaseline.from_dw(pk=kwargs['scenario_id'])

            self.request.session['schema.json'] = ConfigData.objects.filter(type='schema',
                                                                            name='emod-v1.5-schema.txt')[0].json

        if str(self.request.session['scenario'].user) == \
                str(DimUser.objects.get_or_create(username=self.request.user.username)[0]):
            return super(SweepToolView, self).dispatch(request, *args, **kwargs)
        else:
            set_notification('alert-error',
                             'You cannot modify simulations unless you own them.  '
                             'Please select a simulation to work in.',
                             request.session)
            return redirect("ts_emod_scenario_browse")

    def get_template_names(self):
        """ A method to provide the step name/template dictionary """
        TEMPLATES = {"sweep": "ts_emod/sweep_tool.html"}
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, **kwargs):
        """ A method that processes the form data at the end of SweepTool Wizard

            Process then save a run with the collected data
        """

        settings_data = []

        # if this is updating an existing run, add run_id here
        try:
            run_id = int(self.storage.extra_data['edit_run'])
            run = DimRun.objects.get(id=run_id)
            scenario_id = run.baseline_key.id
        except (KeyError, ValueError):
            run_id = -1
            scenario_id = -1

        # Save to Adapter/DW
        adapter = EMOD_Adapter(self.request.user.username)

        my_template = DimTemplate.objects.get(id=self.request.session['scenario'].template.id)

        my_config = ast.literal_eval(self.request.session['scenario'].get_file_by_type('config').content)

        my_start_date = \
            datetime.datetime.strptime(
                my_template.climate_start_date,
                '%Y-%m-%d').date() \
            + datetime.timedelta(days=my_config['parameters']['Start_Time'])
            #+ datetime.timedelta(days=self.request.session['scenario_config']['parameters']['Start_Time'])

        ### Sweeps: u'sweep-sweeps': [u'_4: Acquisition_Blocking_Immunity_Decay_Rate (0.01)'],
        # u'sweep-values': [u'1:2:3']}
        try:
            my_json = dict(self.storage.get_step_data('sweep'))['sweep-sweeps']
            my_values = dict(self.storage.get_step_data('sweep'))['sweep-values']
        except KeyError:
            set_notification('alert-error', '<strong>Error!</strong> The sweep was not saved.',
                             self.request.session)
            return redirect("ts_emod_scenario_details", scenario_id=str(self.request.session['scenario'].id))

        my_run = adapter.save_run(scenario_id=scenario_id,
                                  template_id=int(my_template.id),
                                  start_date=my_start_date,
                                  duration=my_config['parameters']['Simulation_Duration'],
                                  name=self.storage.get_step_data('sweep')['sweep-name'],
                                  description='Created by Sweep Tool',
                                  location_ndx=my_template.location_key.id,
                                  timestep_interval=1,
                                  run_id=run_id,
                                  as_object=True)

        my_run.baseline_key_id = self.request.session['scenario'].id
        my_run.save()

        # add in JCD for it for config file
        changes = []
        newdict = copy.deepcopy(my_config)

        newdict['config.json/parameters'] = newdict.pop('parameters')
        changes.append(Change.node(name='config.json', node=[newdict], mode='-'))

        # add in JCD for campaign file
        my_campaign = ast.literal_eval(self.request.session['scenario'].get_file_by_type('campaign').content)
        if len(my_campaign['Events']) > 0:
            newdict = copy.deepcopy(my_campaign)
            newdict['campaign.json/Use_Defaults'] = newdict.pop('Use_Defaults')
            newdict['campaign.json/Events'] = newdict.pop('Events')
            changes.append(Change.node(name='campaign.json', node=[newdict], mode='-'))

        # move this before saving the run
        ### Sweeps: u'sweep-sweeps': [u'_4: Acquisition_Blocking_Immunity_Decay_Rate (0.01)'],
        # u'sweep-values': [u'1:2:3']}
        # try:
        #     my_json = dict(self.storage.get_step_data('sweep'))['sweep-sweeps']
        #     my_values = dict(self.storage.get_step_data('sweep'))['sweep-values']
        # except KeyError:
        #     set_notification('alert-error', '<strong>Error!</strong> The sweep was not saved.',
        #                      self.request.session)
        #     return redirect("ts_emod_scenario_details", scenario_id=str(self.request.session['scenario'].id))

        for key in my_json:
            path = key.split(':')[2]
            path = path.replace('null/Model Configuration (config.json)', 'config.json')
            path = path.replace('null/Intervention Configuration (campaign.json)', 'campaign.json')
            path = path.replace('null/config', 'config.json')
            path = path.replace('null/campaign', 'campaign.json')
            if 'Events_' in path:
                # Change Events_0 to Events/0 for node list.
                path = path.replace('Events_', 'Events/')
                # remove name from Events/0 name/ segment
                temp = path.split('/')
                temp[2] = temp[2].split(' ')[0]
                path = '/'.join(temp)

            # #3769 - remove leading spaces for this split
            # note: we split by " " (instead of ":") to remove the "(0.01)" default value from the parameter name
            key = key.lstrip().split(' ')[1]
            value = my_values.pop(0)

            settings_data.append(path + key + '=' + value)
            if ':' in value or '|' in value:
                if ':' in value:
                    # ("start", "stop", "step", "xpath")

                    kwargs = {"xpath": path + key, "start": value.split(":")[0],
                              "stop": value.split(":")[1], "step": value.split(":")[2]}
                    changes.append(Change.sweep(name=key, **kwargs))
                else:
                    kwargs = {"xpath": path + key, "l_vals": value.split("|")}
                    changes.append(Change.sweep(name=key, **kwargs))

        my_run.jcd = JCD.from_changes(changes)
        my_run.save()

        set_notification('alert-success', '<strong>Success!</strong> You have successfully saved the sweep ' +
                                          dict(self.storage.get_step_data('sweep'))['sweep-name'][0] + '.',
                         self.request.session)

        # check if user wants to launch, or just save
        if 'launch' in self.storage.data['step_data']['sweep'] \
           and self.storage.data['step_data']['sweep']['launch'][0] == '1':
            launch_flag = True
        else:
            launch_flag = False
        # clear out saved form data.
        self.storage.reset()
        if 'intervention_id' in self.request.session.keys():
            del self.request.session['intervention_id']
        if 'scenario' in self.request.session.keys():
            my_scenario_id = self.request.session['scenario'].id
            del self.request.session['scenario']

        if launch_flag:
            return redirect("ts_emod_launch_tool", step='start', scenario_id=str(my_scenario_id), run_id=str(my_run.id))
        else:
            return redirect("ts_emod_scenario_details", scenario_id=str(my_scenario_id))

    def get_context_data(self, form, **kwargs):
        """Extension of the get_context_data method of the NamedUrlSessionWizardView.
        Select/process initial data based on which step of the Form Wizard it's called for.
        """
        context = super(SweepToolView, self).get_context_data(form=form, **kwargs)

        # Todo: Edit existing sweeps - not sure whether this will be needed, save for later

        if self.steps.current == 'sweep':

            # list of available sweep parameters
            #intervention_list = Intervention.objects.filter(is_public=1)

            #sweeps_available = '{title: "Model Configuration (config.json)", isFolder: true,' \
            #                'children: [' \
            #                    '{title: "parameters",' \
            #                        'children: [' \
            #                            '{title: "Acquisition_Blocking_Immunity_Decay_Rate (0.01)"},' \
            #                            '{title: "Acquisition_Blocking_Immunity_Duration_Before_Decay (90)"},' \
            #                            '{title: "Age_Initialization_Distribution_Type (DISTRIBUTION_SIMPLE)"},' \
            #                            '{title: "Vector_Species_Params", children: [ ' \
            #                                '{title: "farauti", children: [' \
            #                                    '{title: "Acquire_Modifier (0.01)"},' \
            #                                    '{title: "Adult_Life_Expectancy (5.9)"},' \
            #                                    '{title: "Anthropophily (0.97)"}' \
            #                                ']} ' \
            #                            ']}' \
            #                    ']}' \
            #                ']' \
            #            '},' \

            try:
                my_config = ast.literal_eval(self.request.session['scenario'].get_file_by_type('config').content)
            except KeyError:
                my_config = ''

            try:
                my_campaign = ast.literal_eval(self.request.session['scenario'].get_file_by_type('campaign').content)
            except KeyError:
                my_campaign = ''

            # start building tree
            sweeps_available = '{title: "Model Configuration (config.json)", isFolder: true, unselectable: true, ' \
                               'addClass: "root", children: ['
            change_dict = {}
            sweeps_available += walk(my_config, change_dict) + ']},'

            ###
            # handle campaign file
            # do this below and only display campaign option if user selected at least one
            #sweeps_available += '{title: "Intervention Configuration (campaign.json)", isFolder: true, children: ['

            try:
                has_interventions = len(my_campaign)
            except ValueError:
                has_interventions = 0

            if has_interventions > 0:
                # set tree entry for interventions
                sweeps_available += '{title: "Intervention Configuration (campaign.json)", isFolder: true, ' \
                                    'addClass: "root", unselectable: true, children: ['
                sweeps_available += walk(my_campaign, change_dict) + ']}'

            context['sweeps_available'] = sweeps_available

            sweeps_selected = []
            sweep_data = []
            if 'run_id' in kwargs.keys():

                # save the run_id for later use:
                self.storage.extra_data['edit_run'] = int(kwargs['run_id'])

                my_run = DimRun.objects.get(id=kwargs['run_id'])
                context['run_name'] = my_run.name

                for change in my_run.jcd.change_list:
                    if change.type == 'sweep':
                        sweep_data.append(change.jcd_objects[0].jcdict['Changes'][0].values()[0])

                        #sweeps_selected.append(change.jcd_objects[0].jcdict['Changes'][0].keys()[0])
                        path = change.jcd_objects[0].jcdict['Changes'][0].keys()[0]
                        # note: space after parameter name IS required
                        #  - used later to separate out default value "(0.01)" from param name
                        # ToDo: add in default value - or should it be previous value?
                        path = '_0: ' + path.split('/')[-1] + ' :' + path.rsplit('/', 1)[0]

                        # ToDo: add node's id (instead of '_0' above, so the node can be greyed out in selection window
                        # BUT the id's are actually dynatree node's position, no way to know what that will be here...
                        # do in JS of page instead

                        path = path.replace('config.json', 'null/Model Configuration (config.json)')
                        path = path.replace('campaign.json', 'null/Intervention Configuration (campaign.json)')
                        #path = path.replace('config.json', 'null/config')
                        #path = path.replace('campaign.json', 'null/campaign')
                        if 'Events/' in path:
                            # Change Events_0 to Events/0 for node list.
                            path = path.replace('Events/', 'Events_')
                            # remove name from Events/0 name/ segment
                            #temp = path.split('/')
                            #temp[2] = temp[2].split(' ')[0]
                            #path = '/'.join(temp)
                            # #3769 - remove leading spaces for this split
                        #key = key.lstrip().split(' ')[1]

                        path = path + '/'

                        sweeps_selected.append(path)

                context['sweeps_selected'] = json.dumps(sweeps_selected)
                context['sweep_values'] = json.dumps(sweep_data)

            # list of selected sweeps
            try:
                sweep_data = dict(self.storage.get_step_data('sweep'))  # self.get_cleaned_data_for_step('sweep')
                sweeps_selected = sweep_data['sweep-sweeps']
                context['sweeps_selected'] = json.dumps(sweeps_selected)
            except (KeyError, TypeError):
                sweep_data = ''

            # and selected sweep values
            try:
                context['sweep_values'] = json.dumps(sweep_data['sweep-values'])  # json.dumps(sweep_values_list)
            except TypeError:
                pass

            context['scenario'] = self.request.session['scenario']

        return context


## An instance of SweepToolView
#
# Use step names/Forms tuple defined in forms file.
sweep_tool = SweepToolView.as_view(named_sweep_tool_forms,
                                   url_name='ts_sweep_tool_step', done_step_name='complete')


# Todo: make this a library function (it's used in several places now)
def walk(node, change_dict={}):
    """Function to return dynatree children for a JSON oject

    :param node: JSON object
    :returns: dynatree children structure
    """
    text = ''
    if type(node) == dict:
        for key, value in sorted(node.items()):
            if type(value) == dict:
                #print "=====> Parent node: ",  key, 'number of items in dict: ', len(key), type(value)
                text += '{title: "' + key + '", isFolder: true, addClass: "block", children: [ '
                text += walk(value, change_dict)
                text += ']}, '
            else:
                if type(value) == list:
                    #print "LIST: ", key, type(value[0]), value
                    for i in range(len(value)):
                        if type(value[i]) == dict:
                            #for key, value in sorted(value[0].items()):
                            # for intervention Events, add in the event name (my_name) for display to user
                            if key == 'Events':
                                try:
                                    text += '{title: "' + key + '_' + str(i) + ' ' + \
                                            value[i]['Event_Coordinator_Config']['Intervention_Config'][
                                                'my_name'] + '", isFolder: true, addClass: "block", children: [ '
                                except KeyError:
                                    text += '{title: "' + key + '_' + str(i) + ' ' + \
                                            value[i]['Event_Coordinator_Config']['Intervention_Config'][
                                                'class'] + '", children: [ '
                            else:
                                text += '{title: "' + key + '_' + str(i) + '", children: [ '
                            text += walk(value[i], change_dict)
                            text += ']}, '
                        else:
                            if key in change_dict.keys():
                                text += '{title: " ' + key + '_' + str(i) + ' (' + str(change_dict[key]) + ')"' + '}, '
                            else:
                                text += '{title: " ' + key + '_' + str(i) + ' (' + str(value[i]) + ')"' + '}, '
                else:
                #print "Sweep: ", key + ' ('+str(value)+')"'
                #text += '{title: "<strong>'+key + '</strong> ('+str(value)+')"'+'},'
                    #if key == 'Anemia_Mortality_Inverse_Width':
                    if key in change_dict.keys():
                        text += '{title: " ' + key + ' (' + str(change_dict[key]) + ')"' + '}, '
                    else:
                        text += '{title: " ' + key + ' (' + str(value) + ')"' + '}, '
    else:
        print "======= ERROR in TS_EMOD sweep code ======="
        print "Error: ", node
    return text


# Todo: make this a library function (it's used in several places now)
def get_range_from_schema(request):
    if request.GET['name'] is None:
        return HttpResponse('no name specified', mimetype="text/plain")

    name = request.GET['name'].split(' (')[0]       # remove (default) if it exists
    name = name.replace(" ", "")
    path = request.GET['path']
    my_schema = json.loads(request.session['schema.json'])

    # use name and path to find leaf, then get min and max
    if 'config' in path:
        my_dict = get_range_from_node(name, my_schema['config'])
    else:
        my_dict = get_range_from_node(name, my_schema['interventions'])

    range = my_dict['range']
    # make sure we didn't get multiple Ranges into value
    if 'Range' in range:
        try:
            range = "Range: " + range.split("Range: ")[1]
        except ValueError:
            pass
    if 'Choice' in range:
        try:
            range = "Choices: " + range.split("Choices: ")[1]
        except ValueError:
            pass

    my_dict['range'] = range

    desc = my_dict['description']
    if 'Description:' in desc:
        try:
            desc = desc.split("Description:")[1]
        except KeyError:
            pass
    my_dict['description'] = desc

    return HttpResponse(json.dumps(my_dict), mimetype="text/plain")


def get_range_from_node(name, node):
    my_dict = {'range': '', 'description': ''}
    if type(node) == dict:
        for key, value in sorted(node.items()):
            if key == name:
                try:
                    node_type = node[key]['type']
                except KeyError:
                    node_type = None

                if node_type in ['float', 'integer']:
                    my_dict['range'] += "Range: " + str(node[key]['min']) + ' to ' + str(node[key]['max'])
                elif node_type in ['enum']:
                    my_dict['range'] += "Choices: " + str(node[key]['enum']).replace('[u', '').replace(']', '').replace(
                        "', u", ", ").replace("'", "")
                elif node_type in ['bool']:
                    if 'ENABLE' in str(name).upper():
                        my_dict['range'] += "Choices: 1 (for Enabled), 0 (for Disabled)"
                    else:
                        my_dict['range'] += "Choices: 1 (true/on), 0 (false/off)"
                try:
                    my_dict['description'] += "Description:" + node[key]['description']
                except KeyError:
                    my_dict['description'] += "Description:"
                break
            else:
                if type(value) == dict:
                    my_dict['range'] += get_range_from_node(name, value)['range']
                    my_dict['description'] += get_range_from_node(name, value)['description']
                elif type(value) == list:
                    for item in value:
                        my_dict['range'] += get_range_from_node(name, item)['range']
                        my_dict['description'] += get_range_from_node(name, item)['description']
    return my_dict