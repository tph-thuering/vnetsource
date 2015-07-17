########################################################################################################################
# VECNet CI - Prototype
# Date: 03/07/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################
from django.core.exceptions import PermissionDenied
from django.http.response import Http404, HttpResponse
from vecnet.simulation import sim_status
from data_services.adapters.EMOD import EMOD_Adapter
from data_services.data_api import EMODBaseline
from data_services.models import DimRun, DimUser, DimBaseline, Simulation, SimulationInputFile
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from lib.templatetags.base_extras import set_notification
from ts_repr.views.creation.DetailsView import derive_autoname

from data_services.models import *
from data_services.util import *

import ast
import json



class ScenarioDetailView(TemplateView):
    """Class to implement single Baseline detail view

    - Input: scenario ID
    - Output: HTML detail view of that scenario
    """
    template_name = 'ts_emod/scenario/scenario_detail.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        """
        The view part of the view. The method accepts a request argument plus arguments, and returns a HTTP response.
        """
        return super(ScenarioDetailView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Extension of get_context_data

        Add context data to drive menu nav highlights and breadcrumbs.
        """
        context = super(ScenarioDetailView, self).get_context_data(**kwargs)
        context['nav_button'] = "browse_scenario"

        self.request.session['emod_nav_button'] = "browse_scenario"

        # This is here so that Alex can run this later and change all production database entries
        # all_runs = DimRun.objects.all()
        # for run in all_runs:
        #     if run.start_date_key and run.start_date_key.timestamp:
        #         run.new_start_date_key = run.start_date_key.timestamp
        #     if run.end_date_key and run.end_date_key.timestamp:
        #         run.new_end_date_key = run.end_date_key.timestamp
        #     print run.new_start_date_key
        #     print run.new_end_date_key
        #     run.save()

        scenario_id = kwargs['scenario_id']

        scenario = EMODBaseline.from_dw(pk=scenario_id)
        # Hack until DimBaseline/EMODBaseline issues are sorted out
        dim_scenario = DimBaseline.objects.get(id=scenario_id)

        # Hack for calibration
        species_info = {}
        the_config = ast.literal_eval(scenario.get_config_file().content)
        the_species = the_config['parameters']['Vector_Species_Params']
        for specie in the_species:
            species_info[specie] = {}
            if 'EIR' in the_species[specie]:
                eir = the_species[specie]['EIR']
            else:
                eir = 20.0 / float(len(the_species))
            if 'Sporozoite_Rate' in the_species[specie]:
                sporozoite = the_species[specie]['Sporozoite_Rate']
            else:
                sporozoite = 0.003
            species_info[specie]['eir'] = eir
            species_info[specie]['sporozoite'] = sporozoite
        context['species_info'] = species_info
        print species_info
        # data_to_send = {}
        # data_to_send['eir'] = []
        # data_to_send['sporozoite'] = []
        # the_config = ast.literal_eval(scenario.get_config_file().content)
        # the_species = the_config['parameters']['Vector_Species_Params']
        # for i in range(len(the_species)):
        #     data_to_send['eir'].append(20)
        #     data_to_send['sporozoite'].append(0.003)
        # context['data_to_send'] = data_to_send
        if dim_scenario.metadata and 'calibration_status' in dim_scenario.metadata:
            scenario.calibration_status = json.loads(dim_scenario.metadata)['calibration_status']
        else:
            scenario.calibration_status = "Ready"
        if dim_scenario.metadata:
            current_metadata = json.loads(dim_scenario.metadata)
        else:
            current_metadata = {}
        if 'calibration_verification_run_id' in current_metadata:
            calibration_verification_run = DimRun.objects.get(id=current_metadata['calibration_verification_run_id'])

            if calibration_verification_run.status == '1/1/0':
                vector_species_parameters = the_config['parameters']['Vector_Species_Params']
                calibration_verification_info = {}
                for species in vector_species_parameters:
                    calibration_verification_info[species] = {}
                    calibration_verification_info[species]['sporozoite_rate'] = {}
                    calibration_verification_info[species]['eir'] = {}
                    calibration_verification_info[species]['biting_rate'] = {}

                    target_sporozoite_rate = vector_species_parameters[species]['Sporozoite_Rate']
                    daily_sporozoite_rate_2_3 = get_average_daily_sporozoite_rate(calibration_verification_run, species, 2, 3)
                    daily_sporozoite_rate_4_9 = get_average_daily_sporozoite_rate(calibration_verification_run, species, 4, 9)
                    daily_sporozoite_rate_10_20 = get_average_daily_sporozoite_rate(calibration_verification_run, species, 10, 20)

                    calibration_verification_info[species]['sporozoite_rate']['target'] = target_sporozoite_rate
                    calibration_verification_info[species]['sporozoite_rate']['years_2_3'] = daily_sporozoite_rate_2_3
                    calibration_verification_info[species]['sporozoite_rate']['years_4_9'] = daily_sporozoite_rate_4_9
                    calibration_verification_info[species]['sporozoite_rate']['years_10_20'] = daily_sporozoite_rate_10_20

                    target_average_annual_eir = vector_species_parameters[species]['EIR']
                    annual_eir_2_3 = get_average_daily_eir(calibration_verification_run, species, 2, 3) * 365
                    annual_eir_4_9 = get_average_daily_eir(calibration_verification_run, species, 4, 9) * 365
                    annual_eir_10_20 = get_average_daily_eir(calibration_verification_run, species, 10, 20) * 365

                    calibration_verification_info[species]['eir']['target'] = target_average_annual_eir
                    calibration_verification_info[species]['eir']['years_2_3'] = annual_eir_2_3
                    calibration_verification_info[species]['eir']['years_4_9'] = annual_eir_4_9
                    calibration_verification_info[species]['eir']['years_10_20'] = annual_eir_10_20

                    target_average_daily_biting_rate = 'NA'
                    daily_biting_rate_2_3 = get_average_daily_biting_rate(calibration_verification_run, species, 2, 3)
                    daily_biting_rate_4_9 = get_average_daily_biting_rate(calibration_verification_run, species, 4, 9)
                    daily_biting_rate_10_20 = get_average_daily_biting_rate(calibration_verification_run, species, 10, 20)

                    calibration_verification_info[species]['biting_rate']['target'] = target_average_daily_biting_rate
                    calibration_verification_info[species]['biting_rate']['years_2_3'] = daily_biting_rate_2_3
                    calibration_verification_info[species]['biting_rate']['years_4_9'] = daily_biting_rate_4_9
                    calibration_verification_info[species]['biting_rate']['years_10_20'] = daily_biting_rate_10_20

                context['calibration_verification_info'] = calibration_verification_info

        context['scenario_id'] = kwargs['scenario_id']

        context['scenario_userid'] = scenario.user.id
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]

        scenario.last_edited = scenario._last_edited
        scenario.is_public = scenario._is_public

        # Hack until DimBaseline/EMODBaseline issues are sorted out
        if dim_scenario.metadata:
            metadata = json.loads(dim_scenario.metadata)

            if 'representative' in metadata:
                scenario.is_representative = True
                if 'is_complete' in metadata['representative']:
                    scenario.representative_is_completed = True
                else:
                    scenario.representative_is_completed = False
                scenario.name = derive_autoname(dim_scenario)
            else:
                scenario.is_representative = False

        context['scenario'] = scenario

        file_list = []
        for my_file in scenario.files:
            if my_file['type'] == 'config':
                try:
                    context['config'] = json.dumps(ast.literal_eval(scenario.get_file_by_type('config').content),
                                                   sort_keys=True, indent=4, separators=(',', ': '))
                except AttributeError:
                    # if file list was returned, use last file
                    context['config'] = json.dumps(ast.literal_eval(
                        scenario.get_file_by_type('config')[scenario.get_file_by_type('config').count()
                                                               - 1].content), sort_keys=True, indent=4,
                                                   separators=(',', ': '))
            elif my_file['type'] == 'campaign':
                try:
                    scenario_campaign = json.dumps(ast.literal_eval(scenario.get_file_by_type('campaign').content),
                                                   sort_keys=True, indent=4, separators=(',', ': '))
                    if len(json.loads(scenario_campaign)['Events']) > 0:
                        context['campaign'] = scenario_campaign
                    else:
                        context['has_campaign'] = None
                except AttributeError:
                    # if file list was returned, use last file
                    context['campaign'] = json.dumps(ast.literal_eval(
                        scenario.get_file_by_type('campaign')[scenario.get_file_by_type('campaign').count()
                                                                 - 1].content), sort_keys=True, indent=4,
                                                     separators=(',', ': '))
            else:
                file_list.append(my_file['name'])

        context['file_list'] = file_list

        # Get a list of the runs for this scenario
        adapter = EMOD_Adapter(self.request.user.username)
        run_list = DimRun.objects.filter(baseline_key=scenario.id)
        dim_scenario = DimBaseline.objects.get(id=scenario.id)

        if dim_scenario.simulation_group:
            simulation_group = dim_scenario.simulation_group
            simulation_list = Simulation.objects.filter(group=simulation_group)

            for simulation in simulation_list:
                if simulation.status == sim_status.SCRIPT_DONE:
                    simulation.is_complete = True
                elif simulation.status == sim_status.SCRIPT_ERROR:
                    simulation.has_failed = True

            context['simulation_list'] = simulation_list

        # sort descending by id (for those old runs that all have the same old time_created
        context['run_list'] = sorted(run_list, key=lambda x: x.id, reverse=True)
        # sort descending by time_saved
        context['run_list'] = sorted(context['run_list'], key=lambda x: x.time_created, reverse=True)

        note_list = []
        for run in context['run_list']:
            try:
                run_diffs = []

                # config diffs
                run_config = run.jcd.jcdict['config.json']['Changes'][0]['config.json/parameters']
                scenario_config = json.loads(context['config'])['parameters']

                for key in scenario_config:
                    if scenario_config[key] != run_config[key]:
                        run_diffs.append({'key': key, 'run': run_config[key], 'scenario': scenario_config[key]})
                # ToDo: split out each key difference of Vector Species Parameters in both

                # campaign diffs
                if 'campaign.json' not in run.jcd.jcdict:
                    run_diffs.append({'key': 'Interventions', 'run': 'None'})
                else:
                    run_campaign = run.jcd.jcdict['campaign.json']['Changes'][0]['campaign.json/Events']
                    if json.loads(scenario_campaign)['Events'] != run_campaign:
                        run_diffs.append({'key': 'Interventions', 'run': run_campaign,
                                          'scenario': str(json.loads(scenario_campaign)['Events'])})
                    # ToDo: split out each key difference of each Intervention in both
                    # else:
                        # run_diffs.append({'key': 'Interventions', 'run': 'See below',
                        #                 'scenario': '<a class="btn tooltip_link" href="#campaign">see below</a>'})
                run.diffs = run_diffs
            except (AttributeError, KeyError):
                # no JCD?
                run.diffs = [{'Unknown Error Occurred:': 'no changes found.'}]

            # get the status of each run
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

            note_list.extend(adapter.fetch_notes(run_id=int(run.id), as_object=True))

        if note_list != []:
            context['note_list'] = note_list

        return context


def approve_scenario(request, scenario_id):
    """ Method to allow a user to approve a scenario (without going through the wizard) """

    try:
        # get the scenario
        my_scenario = EMODBaseline.from_dw(pk=scenario_id)

        # check for run results
        # ToDo: check for run results

        # set approved, save
        my_scenario.is_approved = True
        my_scenario.save()
        set_notification('alert-success', 'The simulation was approved. ', request.session)
    except:
        set_notification('alert-error', 'An Error occurred: the simulation was not approved. ', request.session)

    return redirect("ts_emod_scenario_details", scenario_id=scenario_id)

def download_csv_file(request, dim_run_id):
    dim_run = DimRun.objects.get(id=dim_run_id)
    csv_output = dim_run.csv_output
    if not csv_output:
        raise Http404()
    dim_user = DimUser.objects.get(username=request.user.username)
    if dim_run.baseline_key.user != dim_user:
        raise PermissionDenied

    response = HttpResponse(content=csv_output.get_contents(),
                            content_type="application/octet-stream")
    response['Content-Disposition'] = 'attachment; filename=output-%s.csv.zip' % dim_run_id

    return response

