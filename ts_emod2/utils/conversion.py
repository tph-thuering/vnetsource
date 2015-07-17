from django.shortcuts import redirect

from vecnet.simulation import sim_model

from data_services.data_api import EMODBaseline
from data_services.models import DimBaseline, SimulationGroup, DimUser, Simulation
from lib.templatetags.base_extras import set_notification
from ts_repr.views.creation.DetailsView import derive_autoname

from ts_emod2.models import Scenario
from ts_emod2.utils.launch import add_simulation

import json


def convert_baseline_to_scenario(request, baseline_id):
    dim_user = DimUser.objects.get(username=request.user.username)
    emod_scenario = EMODBaseline.from_dw(id=baseline_id)
    dim_scenario = DimBaseline.objects.get(id=baseline_id)

    extra_metadata = {}

    # This doesn't all need to be here, but it is simpler just to leave it
    if dim_scenario.metadata:
        metadata = json.loads(dim_scenario.metadata)

        if 'representative' in metadata:
            emod_scenario.is_representative = True
            extra_metadata = metadata
            if 'is_complete' in metadata['representative']:
                emod_scenario.representative_is_completed = True
            else:
                emod_scenario.representative_is_completed = False
            emod_scenario.name = derive_autoname(dim_scenario)
        else:
            emod_scenario.is_representative = False

    # Create simulation group if one is not already made
    if not dim_scenario.simulation_group:
        simulation_group = SimulationGroup(submitted_by=dim_user)
        simulation_group.save()

        simulation = add_simulation(dim_user, sim_model.EMOD, dim_scenario.template.model_version.split('v')[1], simulation_group, baseline_id)

        scenario = Scenario.objects.create(
            name=dim_scenario.name,
            description=dim_scenario.description,
            user=dim_user,
            simulation=simulation,
            metadata={},
            extra_metadata=extra_metadata
        )

        # Modify config
        config_json = json.loads(scenario.config_file.get_contents())
        config_json['parameters']['Land_Temperature_Filename'] = 'temperature.bin'
        config_json['parameters']['Rainfall_Filename'] = 'rainfall.bin'
        config_json['parameters']['Relative_Humidity_Filename'] = 'humidity.bin'
        config_json['parameters']['Air_Temperature_Filename'] = 'temperature.bin'
        config_json['parameters']['Campaign_Filename'] = 'campaign.json'
        config_json['parameters']['Demographics_Filename'] = 'demographics.compiled.json'
        contents = json.dumps(config_json)
        scenario.set_file_by_type('config', contents)

        set_notification('alert-success', '<strong>Success!</strong> Converted baseline to scenario.', request.session)

        # This makes sure we don't try to convert the same baseline twice
        dim_scenario.simulation_group = simulation_group
        dim_scenario.save()
    else:
        simulation_group = dim_scenario.simulation_group
        try:
            simulation = simulation_group.simulations.all()[0]
            scenario = simulation.emod_scenario_set.all()[0]
        except Exception as exception:
            set_notification(
                'alert-error',
                '<strong>Error!</strong> Simulation group exists but there is no matching scenario. ' + str(exception),
                request.session
            )
            return redirect("ts.index")
        set_notification('alert-success', '<strong>Success!</strong> This baseline has already been converted.', request.session)

    return redirect("ts_emod2.details", scenario_id=scenario.id)