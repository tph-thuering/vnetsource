########################################################################################################################
# VECNet CI - Prototype
# Date: 12/10/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################
import datetime
from django.shortcuts import redirect
from data_services.adapters.EMOD import EMOD_Adapter
from data_services.models import DimTemplate, DimRun
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
import ast
import json
import re
from lib.templatetags.base_extras import set_notification


class RunDetailView(TemplateView):
    """Class to implement single Run detail view

    - Input: run ID
    - Output: HTML detail view of that run
    """
    template_name = 'ts_emod/run_detail.html'

    #@method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        The view part of the view. The method accepts a request argument plus arguments, and returns a HTTP response.
        """
        return super(RunDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Extension of get_context_data

        Add context data to drive menu nav highlights and breadcrumbs.
        """
        context = super(RunDetailView, self).get_context_data(**kwargs)
        context['nav_button'] = "browse_scenario"
        the_request = self.request

        the_request.session['emod_nav_button'] = "browse_scenario"
        adapter = EMOD_Adapter(the_request.user.username)

        run_id = kwargs['run_id']
        run = DimRun.objects.get(id=run_id)
        scenario = run.baseline_key
        scenario_id = scenario.id
        context['scenario_id'] = scenario_id
        context['selected_scenario'] = scenario

        context['run'] = run
        context['duration'] = (run.end_date_key - run.start_date_key).days
        context['duration_years'] = (run.end_date_key - run.start_date_key).days / 365

        template_start_date = datetime.datetime.strptime(run.template_key.climate_start_date, '%Y-%m-%d')

        context['start_time_days'] = (template_start_date.date() - run.start_date_key.replace(tzinfo=None).date()).days

        #context['user_changes'] = adapter.fetch_params(run_id=int(my_run.id), as_object=False)

        # get config for the run:
        # - for now, get it from JCD
        for change in run.jcd.change_list:
            if change.type == "node" and change.change_list[0] == '-config.json':
                temp = json.loads(change.jcd_objects[0].json)
                my_config = temp['Changes'][0]['config.json/parameters']

                context['start_time_days'] = my_config['Start_Time']
                context['duration'] = my_config['Simulation_Duration']
                context['duration_years'] = my_config['Simulation_Duration'] / 365

                context['Vector_Species_Names'] = my_config['Vector_Species_Names']

                context['Vector_Species_Params'] = []
                for vector in my_config['Vector_Species_Names']:
                    temp = { 'name': vector, 'params': my_config['Vector_Species_Params'][vector] }
                    context['Vector_Species_Params'].append(temp)

                context['Antigen_Switch_Rate'] = my_config['Antigen_Switch_Rate']
                context['Parasite_Switch_Type'] = my_config['Parasite_Switch_Type']
                context['Falciparum_MSP_Variants'] = my_config['Falciparum_MSP_Variants']
                context['Falciparum_Nonspecific_Types'] = my_config['Falciparum_Nonspecific_Types']
                context['Falciparum_PfEMP1_Variants'] = my_config['Falciparum_PfEMP1_Variants']
                context['New_Diagnostic_Sensitivity'] = my_config['New_Diagnostic_Sensitivity']
                context['Parasite_Smear_Sensitivity'] = my_config['Parasite_Smear_Sensitivity']

                context['x_Temporary_Larval_Habitat'] = my_config['x_Temporary_Larval_Habitat']

        my_changes = set()
        my_sweeps = set()
        my_interventions = []
        my_species_names = {}
        my_species = []
        if run.jcd is None:
            # #5476 - support display of pre-JCD runs (legacy)
            context['old_user_changes'] = adapter.fetch_params(run_id=int(run.id), as_object=False)
        else:
            for change in run.jcd.change_list:
                if change.type == 'atomic':
                    my_changes.add(change.change_list[0].keys()[0] + '=' + str(change.change_list[0].values()[0]))
                elif change.type == 'sweep':
                    my_sweeps.add(change.jcd_objects[0].jcdict['Changes'][0].keys()[0] + '='
                                  + change.jcd_objects[0].jcdict['Changes'][0].values()[0])
                elif change.type == 'node':
                    if change.change_list[0] == '+campaign.json' or change.change_list[0] == '-campaign.json':
                        test = change.jcd_objects[0].jcdict['Changes'][0]
                        try:
                            test['Events'] = test.pop('campaign.json/Events')
                            test['Use_Defaults'] = test.pop('campaign.json/Use_Defaults')
                        except KeyError:
                            pass
                        my_interventions.append(test)  # change.jcd_objects[0].jcdict['Changes'][0]['Changes'][0])
                        #  load Species from run
                    #    my_species_names = change.jcd_objects[0].jcdict['Changes'][0].values()[0]
                    elif re.match('.+Vector_Species_Params.+', change.jcd_objects[0].jcdict['Changes'][0].keys()[0]):
                        for each_species in change.jcd_objects[0].jcdict['Changes'][0].keys():
                            my_species.append(" ")
                            my_species.append("Name=" + each_species.split("/")[-1])
                            for key in change.jcd_objects[0].jcdict['Changes'][0][each_species].keys():
                                my_species.append(key + '=' +
                                                  str(change.jcd_objects[0].jcdict['Changes'][0][each_species][key]))

        context['user_changes_atomic'] = my_changes
        context['user_changes_sweeps'] = my_sweeps
        if my_interventions:
            context['user_changes_interventions'] = str(my_interventions[0]).replace("u'", '"').replace("'", '"')
        else:
            context['user_changes_interventions'] = {}
        context['user_changes_species'] = my_species
        context['user_changes_species_names'] = my_species_names

        context['notes'] = adapter.fetch_notes(run_id=int(run.id), as_object=True)

        try:
            my_files = run.get_input_files()
            context['campaign'] = json.dumps(ast.literal_eval(my_files['campaign.json']),
                                             sort_keys=True, indent=4, separators=(',', ': '))
            context['config'] = json.dumps(ast.literal_eval(my_files['config.json']),
                                           sort_keys=True, indent=4, separators=(',', ': '))
        except KeyError:
            pass

        # template 9 replaced template 4
        if run.template_key_id == 4 or int(run.template_key_id) == 4:
            run.template_key_id = 9

        context['template_id'] = run.template_key_id
        my_temp_list = adapter.fetch_template_list()
        for my_id in my_temp_list:
            if my_id == int(run.template_key_id):
                context['template_name'] = my_temp_list[my_id]['name']
                context['template_description'] = my_temp_list[my_id]['description']

        my_temp = DimTemplate.objects.get(id=int(run.template_key_id))
        context["climate_url"] = my_temp.climate_url

        # get the status of the run
        adapter = EMOD_Adapter(self.request.user.username)
        status = adapter.run_status(run.id)
        if status is None:
            run.my_completed = None
        else:
            run.my_completed = status[0]
            run.my_total = status[1]
            run.my_failed = status[2]
            run.percent_complete = (run.my_completed + run.my_failed) / run.my_total
            run.my_incomplete = int(run.my_total) - (int(run.my_completed) + int(run.my_failed))
            if int(status[0]) > 0:
                context['has_results'] = 1

            run.errors = adapter.fetch_errors(run.id)
            context['my_run'] = run

        return context


def duplicateRun(request, run_id):
    """ Function to allow duplication of run DB Objects """
    if not request.user.is_authenticated():
        set_notification('alert-error', '<strong>Error!</strong> Please log in before duplicating. '
                                        'Run was not duplicated.', request.session)
    else:
        # Save a copy of the run to Adapter/DW
        old_run = DimRun.objects.get(id=run_id)
        try:
            adapter = EMOD_Adapter(request.user.username)

            # NOTES - dimnotes_set
            my_notes = ''
            for i in old_run.dimnotes_set.values_list():
                my_notes += ' - '+i[2]

            new_run = adapter.save_run(scenario_id=old_run.baseline_key_id,
                                       template_id=old_run.template_key_id,
                                       start_date=old_run.start_date_key,
                                       end_date=old_run.end_date_key,
                                       name=old_run.name + ' duplicate',
                                       description=old_run.description + ' duplicate',
                                       location_ndx=old_run.location_key_id,
                                       timestep_interval=old_run.timestep_interval_days,
                                       note=my_notes,
                                       as_object=True)

            new_run.jcd = old_run.jcd
            new_run.save()

            set_notification('alert-success', '<strong>Success!</strong> You have successfully duplicated the run '
                                              + old_run.name + '.', request.session)
        except:
            print 'Error saving the duplicate run for scenario: %s' % request.session['selected_scenario'].name
            set_notification('alert-error', '<strong>Error!</strong> Error duplicating the run for scenario ' +
                             request.session['selected_scenario'].name + '.', request.session)

    return redirect(request.environ['HTTP_REFERER'])