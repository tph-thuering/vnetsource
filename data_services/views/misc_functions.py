from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from VECNet.settings import EMOD_BASELINE_UPDATE_BASELINE_API_KEY, SITE_ROOT_URL, CONFIG_CALIBRATION_URL
from lib.templatetags.base_extras import set_notification
from vecnet.simulation import sim_model, sim_status

from data_services.data_api import EMODBaseline
from data_services.models import DimUser, DimBaseline, SimulationGroup, Simulation, SimulationInputFile

import ast
import json
import requests
from requests.packages.urllib3.exceptions import ConnectionError, HTTPError


@csrf_exempt
def update_emod_config(request, scenario_id):
    # Check if api key was supplied
    try:
        api_key = request.POST['api_key']
    except KeyError:
        return HttpResponse(content=json.dumps({'Error': 'api_key missing in POST request'}))

    # Check if the supplied api key is valid
    if api_key != EMOD_BASELINE_UPDATE_BASELINE_API_KEY:
        return HttpResponse(content=json.dumps({'Error': 'The api_key that was provided is invalid'}))

    # Check if the supplied scenario id is valid
    try:
        emod_scenario = EMODBaseline.from_dw(id=scenario_id)
    except ObjectDoesNotExist:
        return HttpResponse(content=json.dumps({'Error': 'Scenario with id ' + str(scenario_id) + ' does not exist.'}))
    except Exception as exception:
        return HttpResponse(content=json.dumps({'Error': 'Unhandled exception: ' + str(exception)}))

    # Check if a message was supplied
    try:
        message = request.POST['message']
    except KeyError:
        return HttpResponse(content=json.dumps({'Error': 'message missing in POST request'}))

    # This variable and if statement is just a place holder for what we could have later if we allow users to access this api
    CALIBRATION_API_KEY = EMOD_BASELINE_UPDATE_BASELINE_API_KEY

    # Handle the message
    if message == 'success':
        # Check if a config was supplied
        if 'config' not in request.POST:
            return HttpResponse(content=json.dumps({'Error': 'config missing in POST request'}))

        # Check if the config is valid json
        try:
            calibrated_config_json = json.loads(request.POST['config'])
        except:
            return HttpResponse(content=json.dumps({'Error': 'The json that was provided is invalid'}))

        merged_config_json = ast.literal_eval(emod_scenario.get_config_file().content)
        merged_config_json['parameters']['Vector_Species_Params'] = calibrated_config_json['parameters']['Vector_Species_Params']

        # Add the new config
        emod_scenario.add_file_from_string('config', 'config.json', json.dumps(merged_config_json), description='SOMETHING')
        emod_scenario.save()

        # Set the calibration status if applicable
        calibration_status = 'complete'
    elif message == 'failure':
        # Set the calibration status if applicable
        calibration_status = 'failed'
    else:
        return HttpResponse(content=json.dumps({'Error': 'The message that was provided is invalid. Should be either "success" or "failure"'}))

    if (api_key == CALIBRATION_API_KEY):
        # Yet another hack until DimBaseline vs EMODBaseline issues are resolved
        dim_scenario = DimBaseline.objects.get(id=scenario_id)

        # This catches any simulations that don't have metadata set yet
        try:
            current_metadata = json.loads(dim_scenario.metadata)  # Need to double check if the loading and dumping is necessary
        except ValueError:
            current_metadata = {}

        current_metadata['calibration_status'] = calibration_status
        dim_scenario.metadata = json.dumps(current_metadata)
        dim_scenario.save()

    return HttpResponse(content=json.dumps({'Success': 'The config json was successfully changed'}))


def send_calibration_request(request, targets, scenario_id):
    dim_scenario = DimBaseline.objects.get(id=scenario_id)

    # Get user
    user = DimUser.objects.get_or_create(username=request.user.username)[0]

    # Check user
    #if dim_scenario.user != user:
    #    raise PermissionDenied

    # Create simulation group
    simulation_group = SimulationGroup(submitted_by=user)
    simulation_group.save()

    # Create emod_scenario for helper functions to get files
    emod_scenario = EMODBaseline.from_dw(id=scenario_id)

    # Create input files and put them into a list
    simulation_input_files = create_and_return_input_files(user, emod_scenario)

    # Get version
    try:
        # Slices off the excess and leaves just the version number
        version = emod_scenario.template.model_version.split('v')[1]
    except:
        version = 'unknown'

    # Create simulation
    simulation = Simulation.objects.create(
        group=simulation_group,
        model=sim_model.EMOD_CALIBRATION,
        version=version,
        status=sim_status.READY_TO_RUN
    )

    file_urls = {}

    # Add simulation input files to simulation
    for i in range(len(simulation_input_files)):
        simulation.input_files.add(simulation_input_files[i])
        file_urls[simulation_input_files[i].name] = SITE_ROOT_URL[:-1] + reverse(
            'input_file_download',
            kwargs={
                'resource_name': 'input_files',
                'pk': simulation_input_files[i].id,
                'api_name': 'v1'
            }
        )

    print "targets = " + json.dumps(targets)
    print file_urls

    data = {}
    data['targets'] = json.dumps(targets)
    data['files'] = json.dumps(file_urls)
    data['url'] = SITE_ROOT_URL[:-1] + reverse('data_services.update_emod_config', kwargs={'scenario_id': scenario_id})
    data['version'] = version

    print data

    url = CONFIG_CALIBRATION_URL

    try:
        send_request = requests.post(url, data=data)
    except ConnectionError:
        set_notification('alert-error', '<strong>Error!</strong> Connection error with calibration service.', request.session)
        return

    print send_request.status_code

    try:
        current_metadata = json.loads(dim_scenario.metadata)
    except:
        current_metadata = {}

    if str(send_request.status_code) == "200":
        current_metadata['calibration_status'] = 'sent'
    else:
        current_metadata['calibration_status'] = 'failed'

    dim_scenario.metadata = json.dumps(current_metadata)
    dim_scenario.save()

    if current_metadata['calibration_status'] == 'failed':
        set_notification('alert-error', '<strong>Error!</strong> Request error with calibration service.', request.session)
        return

    set_notification('alert-success', '<strong>Success!</strong> Calibration request sent.', request.session)


@csrf_exempt
def send_calibration_request_ajax(request, scenario_id):
    try:
        unformatted_targets_json = json.loads(request.body)
    except:
        set_notification('alert-error', '<strong>Error!</strong> Malformed request.body json.', request.session)
        return HttpResponse()

    targets_json = {}
    targets_json['sporozoite'] = []
    targets_json['eir'] = []

    for species in unformatted_targets_json:
        targets_json['sporozoite'].append(unformatted_targets_json[species]['sporozoite'])
        targets_json['eir'].append(unformatted_targets_json[species]['eir'])

    send_calibration_request(request, targets_json, scenario_id)

    return HttpResponse()


def create_and_return_input_files(dim_user, emod_scenario):
    metadata = {}
    should_get_json = True
    should_get_bin = True

    config_json = ast.literal_eval(emod_scenario.get_config_file().content)

    campaign_filename = 'campaign.json' #config_json['parameters']['Campaign_Filename']
    compiled_demographics_filename = 'demographics.compiled.json' #config_json['parameters']['Demographics_Filename']
    uncompiled_demographics_filename = 'demographics.json'
    temperature_filename = 'temperature.bin' #config_json['parameters']['Air_Temperature_Filename']
    humidity_filename = 'humidity.bin' #config_json['parameters']['Relative_Humidity_Filename']
    rainfall_filename = 'rainfall.bin' #config_json['parameters']['Rainfall_Filename']

    # Create config simulation input file
    config_simulation_file = SimulationInputFile.objects.create_file(
        contents=json.dumps(ast.literal_eval(emod_scenario.get_config_file().content)),
        name='config.json',
        metadata=metadata,
        created_by=dim_user
    )

    # Create campaign simulation input file
    campaign_simulation_file = SimulationInputFile.objects.create_file(
        contents=json.dumps(ast.literal_eval(emod_scenario.get_campaign_file().content)),
        name=campaign_filename,
        metadata=metadata,
        created_by=dim_user
    )

    # Create demographics input file
    demographics_simulation_input_file = SimulationInputFile.objects.create_file(
        contents=emod_scenario.get_demographics_file().content,
        name=compiled_demographics_filename,
        metadata=metadata,
        created_by=dim_user
    )

    uncompiled_demographics_simulation_input_file = SimulationInputFile.objects.create_file(
        contents=emod_scenario.get_uncompiled_demographics_file(),
        name=uncompiled_demographics_filename,
        metadata=metadata,
        created_by=dim_user
    )

    # Create weather simulation input files
    rainfall_json_simulation_file = SimulationInputFile.objects.create_file(
        contents=json.dumps(ast.literal_eval(emod_scenario.get_rainfall_file(not should_get_bin, should_get_json).content)),
        name=rainfall_filename + '.json',
        metadata=metadata,
        created_by=dim_user
    )

    rainfall_bin_simulation_file = SimulationInputFile.objects.create_file(
        contents=emod_scenario.get_rainfall_file(should_get_bin, not should_get_json).content,
        name=rainfall_filename,
        metadata=metadata,
        created_by=dim_user
    )

    humidity_json_simulation_file = SimulationInputFile.objects.create_file(
        contents=json.dumps(ast.literal_eval(emod_scenario.get_humidity_file(not should_get_bin, should_get_json).content)),
        name=humidity_filename + '.json',
        metadata=metadata,
        created_by=dim_user
    )

    humidity_bin_simulation_file = SimulationInputFile.objects.create_file(
        contents=emod_scenario.get_humidity_file(should_get_bin, not should_get_json).content,
        name=humidity_filename,
        metadata=metadata,
        created_by=dim_user
    )

    temperature_json_simulation_file = SimulationInputFile.objects.create_file(
        contents=json.dumps(ast.literal_eval(emod_scenario.get_air_file(not should_get_bin, should_get_json).content)),
        name=temperature_filename + '.json',
        metadata=metadata,
        created_by=dim_user
    )

    temperature_bin_simulation_file = SimulationInputFile.objects.create_file(
        contents=emod_scenario.get_air_file(should_get_bin, not should_get_json).content,
        name=temperature_filename,
        metadata=metadata,
        created_by=dim_user
    )

    simulation_input_files = [
        demographics_simulation_input_file,
        uncompiled_demographics_simulation_input_file,
        rainfall_json_simulation_file,
        rainfall_bin_simulation_file,
        humidity_json_simulation_file,
        humidity_bin_simulation_file,
        temperature_json_simulation_file,
        temperature_bin_simulation_file,
        config_simulation_file,
        campaign_simulation_file
    ]

    return simulation_input_files


# def create_and_return_input_files2(dim_user, simulation):
#     metadata = {}
#
#     config_filename = 'config.json'
#     campaign_filename = 'campaign.json'
#     compiled_demographics_filename = 'demographics.compiled.json'
#     uncompiled_demographics_filename = 'demographics.json'
#     temperature_filename = 'temperature.bin'
#     humidity_filename = 'humidity.bin'
#     rainfall_filename = 'rainfall.bin'
#
#     # Create config simulation input file
#     config_simulation_file = SimulationInputFile.objects.create_file(
#         contents=get_config_file(dim_user, simulation).get_contents(),
#         name=config_filename,
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     # Create campaign simulation input file
#     campaign_simulation_file = SimulationInputFile.objects.create_file(
#         contents=get_campaign_file(dim_user, simulation).get_contents(),
#         name=campaign_filename,
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     # Create demographics input file
#     compiled_demographics_simulation_input_file = SimulationInputFile.objects.create_file(
#         contents=get_compiled_demographics_file(dim_user, simulation).get_contents(),
#         name=compiled_demographics_filename,
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     uncompiled_demographics_simulation_input_file = SimulationInputFile.objects.create_file(
#         contents=get_uncompiled_demographics_file(dim_user, simulation).get_contents(),
#         name=uncompiled_demographics_filename,
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     # Create weather simulation input files
#     rainfall_json_simulation_file = SimulationInputFile.objects.create_file(
#         contents=get_rainfall_json_file(dim_user, simulation).get_contents(),
#         name=rainfall_filename + '.json',
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     rainfall_bin_simulation_file = SimulationInputFile.objects.create_file(
#         contents=get_rainfall_bin_file(dim_user, simulation).get_contents(),
#         name=rainfall_filename,
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     humidity_json_simulation_file = SimulationInputFile.objects.create_file(
#         contents=get_humidity_json_file(dim_user, simulation).get_contents(),
#         name=humidity_filename + '.json',
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     humidity_bin_simulation_file = SimulationInputFile.objects.create_file(
#         contents=get_humidity_bin_file(dim_user, simulation).get_contents(),
#         name=humidity_filename,
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     temperature_json_simulation_file = SimulationInputFile.objects.create_file(
#         contents=get_temperature_json_file(dim_user, simulation).get_contents(),
#         name=temperature_filename + '.json',
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     temperature_bin_simulation_file = SimulationInputFile.objects.create_file(
#         contents=get_temperature_bin_file(dim_user, simulation).get_contents(),
#         name=temperature_filename,
#         metadata=metadata,
#         created_by=dim_user
#     )
#
#     simulation_input_files = [
#         compiled_demographics_simulation_input_file,
#         uncompiled_demographics_simulation_input_file,
#         rainfall_json_simulation_file,
#         rainfall_bin_simulation_file,
#         humidity_json_simulation_file,
#         humidity_bin_simulation_file,
#         temperature_json_simulation_file,
#         temperature_bin_simulation_file,
#         config_simulation_file,
#         campaign_simulation_file
#     ]
#
#     return simulation_input_files