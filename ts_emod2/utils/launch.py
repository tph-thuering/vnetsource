from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from vecnet.simulation import sim_model, sim_status
from data_services.data_api import EMODBaseline
from lib.templatetags.base_extras import set_notification
from sim_services import dispatcher

from data_services.models import DimUser, SimulationGroup, Simulation
from data_services.views.misc_functions import create_and_return_input_files

from ts_emod2.models import Scenario

import json


def launch_scenario(request, scenario_id):
    dim_user = DimUser.objects.get(username=request.user.username)
    scenario = Scenario.objects.get(id=scenario_id)

    config_json = json.loads(scenario.config_file.get_contents())

    print config_json['parameters']['Land_Temperature_Filename']
    print config_json['parameters']['Rainfall_Filename']
    print config_json['parameters']['Relative_Humidity_Filename']
    print config_json['parameters']['Air_Temperature_Filename']
    print config_json['parameters']['Campaign_Filename']
    print config_json['parameters']['Demographics_Filename']

    # config_json['parameters']['Land_Temperature_Filename'] = 'temperature.bin'
    # config_json['parameters']['Rainfall_Filename'] = 'rainfall.bin'
    # config_json['parameters']['Relative_Humidity_Filename'] = 'humidity.bin'
    # config_json['parameters']['Air_Temperature_Filename'] = 'temperature.bin'
    # config_json['parameters']['Campaign_Filename'] = 'campaign.json'
    # config_json['parameters']['Demographics_Filename'] = 'demographics.compiled.json'
    config_json['parameters']['Simulation_Duration'] = 100

    try:
        scenario.set_file_by_type('config', json.dumps(config_json))
    except RuntimeError as error:
        set_notification('alert-error', '<strong>Error!</strong> ' + str(error), request.session)
        return redirect("ts_emod2.details", scenario_id=scenario_id)

    submit(request, sim_model.EMOD, scenario_id)

    set_notification('alert-success', '<strong>Success!</strong> Job submitted.', request.session)

    return redirect("ts_emod2.details", scenario_id=scenario_id)


def submit(request, model, scenario_id):
    dim_user = DimUser.objects.get(username=request.user.username)
    scenario = Scenario.objects.get(id=scenario_id)
    simulation = scenario.simulation
    simulation_group = simulation.group

    # Check if this is the right user for this scenario
    if scenario.user != dim_user:
        raise PermissionDenied

    dispatcher.submit(simulation_group)


def add_simulation(dim_user, model, version, simulation_group, baseline_id, input_file_metadata=None):
    assert isinstance(simulation_group, SimulationGroup)

    emod_scenario = EMODBaseline.from_dw(id=baseline_id)

    # Check if this is the right user for this scenario. All three should be the same. If the dim_scenario user
    # and the simulation_group user are the same, and if user coming in is the same dis_scenario user, then all
    # three are the same user.
    if emod_scenario.user != simulation_group.submitted_by or dim_user != emod_scenario.user:
        raise PermissionDenied

    # Create simulation
    simulation = Simulation.objects.create(
        group=simulation_group,
        model=model,
        version=version,
        status=sim_status.READY_TO_RUN
    )

    # Create input files and put them into a list
    simulation_input_files = create_and_return_input_files(dim_user, emod_scenario)

    # Add simulation input files to simulation
    for i in range(len(simulation_input_files)):
        simulation.input_files.add(simulation_input_files[i])

    simulation.save()

    return simulation