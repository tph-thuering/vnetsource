from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from data_services.adapters import EMOD_Adapter
from data_services.data_api import EMODBaseline
from data_services.models import DimModel, DimUser, DimTemplate, DimBaseline

from lib.templatetags.base_extras import set_notification

from ts_repr.models import RepresentativeScenario, RepresentativeWeather, RepresentativeDemographics, \
    RepresentativeSpecies, RepresentativeSpeciesParameter, EMODSnippet

import json
from datetime import datetime

BEGIN_STEP = 0
WEATHER_STEP = 1
DEMOGRAPHICS_STEP = 2
SPECIES_STEP = 3
PARASITE_STEP = 4
DETAILS_STEP = 5


def determine_page(request, scenario_id):
    scenario = DimBaseline.objects.get(id=scenario_id)
    current_metadata = json.loads(scenario.metadata)

    try:
        steps_complete = current_metadata['representative']['steps_complete']
    except:
        steps_complete = 1

    kwargs = {'scenario_id': scenario_id}

    if steps_complete == BEGIN_STEP or not steps_complete:
        url = 'ts_repr.new_scenario'
        kwargs = {}
    elif steps_complete == WEATHER_STEP:
        url = 'ts_repr.weather'
    elif steps_complete == DEMOGRAPHICS_STEP:
        url = 'ts_repr.demographics'
    elif steps_complete == SPECIES_STEP:
        url = 'ts_repr.species'
    elif steps_complete == PARASITE_STEP:
        url = 'ts_repr.parasite'
    elif steps_complete == DETAILS_STEP:
        url = 'ts_repr.details'
    else:
        raise ValueError("Scenario with id " + str(scenario_id) +
                         " has an invalid steps_complete of " + str(steps_complete) + ".")

    return HttpResponseRedirect(reverse(url, kwargs=kwargs))


@never_cache
@csrf_exempt
def create_emod_scenario(request, representative_id):
    # Retrieve all saved data from the RepresentativeScenario
    representative_scenario = RepresentativeScenario.objects.get(id=representative_id)
    current_json = json.loads(representative_scenario.choices)
    simulation_name = representative_scenario.name
    weather_data = get_weather(current_json['weather_id'])
    demographics_data = get_demographics(current_json['demographics_id'])
    species = get_species(current_json['species_page']['species'])

    adapter = EMOD_Adapter(request.user.username)

    emod_scenario = EMODBaseline(
        name=simulation_name,
        description='Made with representative workflow',
        model=DimModel.objects.get(model='EMOD'),
        user=DimUser.objects.get_or_create(username=request.user.username)[0]
    )

    template_object = DimTemplate.objects.get(id=21)

    emod_scenario.model_version = template_object.model_version
    emod_scenario.template_id = 21
    emod_scenario.template = template_object

    # Populate config
    config_json = json.loads(template_object.get_file_content('config.json'))

    # Change config
    config_json['parameters']['Rainfall_Filename'] = weather_data['file_locations']['rainfall']
    config_json['parameters']['Relative_Humidity_Filename'] = weather_data['file_locations']['humidity']
    config_json['parameters']['Air_Temperature_Filename'] = weather_data['file_locations']['temperature']
    config_json['parameters']['Land_Temperature_Filename'] = weather_data['file_locations']['temperature']

    config_json['parameters']['Demographics_Filename'] = demographics_data['file_location']

    for i in range(len(species)):
        config_json['parameters']['Vector_Species_Names'].append(species[i]['name'].lower())
        config_json['parameters']['Vector_Species_Params'][species[i]['name'].lower()] = \
            json.loads(species[i]['snippet'])[species[i]['name'].lower()]

    print json.dumps(config_json)

    # Attach the emod_scenario config file
    emod_scenario.add_file_from_string('config', 'config.json', json.dumps(config_json), description='SOMETHING')

    # populate campaign
    try:
        campaign = json.loads(template_object.get_file_content('campaign.json'))
    except KeyError:
        # use empty campaign file
        campaign = json.loads({"Events": []})

    # Add the emod_scenario campaign file
    emod_scenario.add_file_from_string('campaign', 'campaign.json', json.dumps(campaign), description='SOMETHING')

    # Add the weather
    emod_scenario.add_file_from_string('rainfall json', 'rainfall.json', weather_data['file_data']['rainfall']['json'], description='SOMETHING')
    emod_scenario.add_file_from_string('rainfall binary', 'rainfall.bin', weather_data['file_data']['rainfall']['bin'], description='SOMETHING')
    emod_scenario.add_file_from_string('humidity json', 'humidity.json', weather_data['file_data']['humidity']['json'], description='SOMETHING')
    emod_scenario.add_file_from_string('humidity binary', 'humidity.bin', weather_data['file_data']['humidity']['bin'], description='SOMETHING')
    emod_scenario.add_file_from_string('air json', 'temperature.json', weather_data['file_data']['temperature']['json'], description='SOMETHING')
    emod_scenario.add_file_from_string('air binary', 'temperature.bin', weather_data['file_data']['temperature']['bin'], description='SOMETHING')

    # Add land temperature
    emod_scenario.add_file_from_string('land_temp json', 'temperature.json', weather_data['file_data']['temperature']['json'], description='SOMETHING')
    emod_scenario.add_file_from_string('land_temp binary', 'temperature.bin', weather_data['file_data']['temperature']['bin'], description='SOMETHING')

    # Add the demographics
    emod_scenario.add_file_from_string('demographics', 'demographics.compiled.json', demographics_data['file_data'], description='SOMETHING')

    emod_scenario.save()

    representative_scenario.emod_scenario = DimBaseline.objects.get(id=emod_scenario.id)  # This needs to be checked. Not sure what EMODBaseline is
    representative_scenario.save()

    return redirect("ts_emod_scenario_details", scenario_id=emod_scenario.id)


def get_weather(weather_id):
    if weather_id == 0:
        return "Custom"

    weather = RepresentativeWeather.objects.get(id=weather_id)
    weather_data = {}
    rainfall_json = "{}"
    rainfall_bin = ""
    humidity_json = "{}"
    humidity_bin = ""
    temperature_json = "{}"
    temperature_bin = ""

    for weather_file in weather.emod_weather.all():
        if ".bin" in weather_file.name:
            if "rainfall" in weather_file.name:
                rainfall_bin = weather_file.get_contents()
            if "humidity" in weather_file.name:
                humidity_bin = weather_file.get_contents()
            if "temperature" in weather_file.name:
                temperature_bin = weather_file.get_contents()
        elif ".json" in weather_file.name:
            if "rainfall" in weather_file.name:
                rainfall_json = weather_file.get_contents()
            if "humidity" in weather_file.name:
                humidity_json = weather_file.get_contents()
            if "temperature" in weather_file.name:
                temperature_json = weather_file.get_contents()
        else:
            raise TypeError("The weather file named " + weather_file.name + " is not a valid file. " +
                            "Should be a bin or json.")

    weather_data['file_data'] = {}
    weather_data['file_locations'] = {}

    weather_data['file_data']['rainfall'] = {'json': rainfall_json, 'bin': rainfall_bin}
    weather_data['file_data']['humidity'] = {'json': humidity_json, 'bin': humidity_bin}
    weather_data['file_data']['temperature'] = {'json': temperature_json, 'bin': temperature_bin}

    weather_data['file_locations']['rainfall'] = weather.emod_weather_rainfall_file_location
    weather_data['file_locations']['humidity'] = weather.emod_weather_humidity_file_location
    weather_data['file_locations']['temperature'] = weather.emod_weather_temperature_file_location

    return weather_data


def get_demographics(demographics_id):
    demographics = RepresentativeDemographics.objects.get(id=demographics_id)

    demographics_data = {}
    demographics_data['file_data'] = demographics.emod_demographics_compiled.get_contents()
    demographics_data['file_location'] = demographics.emod_demographics_compiled_file_location

    return demographics_data


def get_species_data(species_id):
    if int(species_id) == 0:
        return -1

    species_data = {}
    species = RepresentativeSpecies.objects.get(id=species_id)

    species_data['description'] = species.description
    species_data['is_active'] = species.is_active
    species_data['name_for_users'] = species.name

    if species.emod_snippet:
        species_name = species.emod_snippet.name
        species_data['name_in_code'] = species_name

        species_data['emod_snippet_id'] = species.emod_snippet.id
        species_data['emod_snippet'] = species.emod_snippet.snippet
        species_json = json.loads(species.emod_snippet.snippet)  # Using json.loads until we switch to JSONField instead of JSONConfigField

        species_data['parameters'] = [{}, {}, {}, {}, {}, {}]

        for i in range(len(species_data['parameters'])):
            species_data['parameters'][i]['is_list'] = False

        species_data['parameters'][0]['name'] = 'Anthropophily'
        species_data['parameters'][0]['value'] = species_json[species_name]['Anthropophily']

        species_data['parameters'][1]['name'] = 'Indoor Feeding Preference'
        species_data['parameters'][1]['value'] = species_json[species_name]['Indoor_Feeding_Fraction']

        species_data['parameters'][2]['name'] = 'Gonotrophic Cycle @ 30C'
        species_data['parameters'][2]['value'] = species_json[species_name]['Days_Between_Feeds']

        species_data['parameters'][3]['name'] = 'Sporozoite Rate'
        species_data['parameters'][3]['value'] = species_json[species_name]['Sporozoite_Rate'] if ('Sporozoite_Rate' in species_json[species_name]) else 'Undefined'

        species_data['parameters'][4]['name'] = 'Larval Habitat'
        species_data['parameters'][4]['value'] = species_json[species_name]['Habitat_Type']
        species_data['parameters'][4]['is_list'] = True

        species_data['parameters'][5]['name'] = 'Daily Survival Rate'
        species_data['parameters'][5]['value'] = 1 - (1 / float(species_json[species_name]['Adult_Life_Expectancy']))
    else:
        species_data['name'] = species.name
        species_data['emod_snippet_id'] = 0
        species_data['emod_snippet'] = 'No Snippet'

    if species.om_snippet:
        species_data['om_snippet_id'] = species.om_snippet.id
        species_data['om_snippet'] = species.om_snippet.snippet
    else:
        species_data['om_snippet_id'] = 0
        species_data['om_snippet'] = 'No Snippet'

    return species_data


def get_species(species_json):
    print species_json
    return temp_get_species(species_json)  # Temporary skip of parameters gathering

    # Add information that isn't stored in the json. This will allow the backend to load up this information in
    # a nice and easy way before it hands it off to the frontend. This way the frontend won't have to make extra
    # calls back to the backend for the missing information.
    for species in species_json:
        representative_species = RepresentativeSpecies.objects.get(id=species['species_id'])
        species['name'] = representative_species.name

        for parameter in species['parameters']:
            representative_parameter = RepresentativeSpeciesParameter.objects.get(id=parameter['id'])
            parameter['name'] = representative_parameter.name
            parameter['emod_value'] = get_parameter_value(parameter['choice'], representative_parameter, 'emod')
            parameter['om_value'] = get_parameter_value(parameter['choice'], representative_parameter, 'om')

    print species_json
    return species_json


def temp_get_species(species_json):
    species_data = []

    for species in species_json:
        representative_species = RepresentativeSpecies.objects.get(id=species['species_id'])
        species_data.append(representative_species)
        # species_data.append({})
        # species_data[len(species_data) - 1]['name'] = representative_species.name
        # species_data[len(species_data) - 1]['snippet'] = representative_species.emod_snippet.snippet

    return species_data


def get_parameter_value(choice, parameter, model):
    if model == 'emod':
        if choice == 'high':
            return parameter.emod_high
        elif choice == 'medium':
            return parameter.emod_medium
        elif choice == 'low':
            return parameter.emod_low
    elif model == 'om':
        if choice == 'high':
            return parameter.om_high
        elif choice == 'medium':
            return parameter.om_medium
        elif choice == 'low':
            return parameter.om_low


@never_cache
@csrf_exempt
def get_emod_snippet_ajax(request, option_id):
    emod_snippet_data = get_emod_snippet(option_id)

    return HttpResponse(content=json.dumps(emod_snippet_data), content_type='application/json')


def get_emod_snippet(snippet_id):
    if int(snippet_id) == 0:
        return -1

    emod_snippet_data = {}
    emod_snippet = EMODSnippet.objects.get(id=snippet_id)

    emod_snippet_data['name_for_config_file'] = emod_snippet.name
    emod_snippet_data['description'] = emod_snippet.description

    emod_snippet_data['emod_snippet_id'] = emod_snippet.id
    emod_snippet_data['emod_snippet'] = emod_snippet.snippet

    print emod_snippet_data

    return emod_snippet_data


@never_cache
@csrf_exempt
def get_om_snippet_ajax(request, option_id):
    om_snippet_data = get_om_snippet(option_id)

    return HttpResponse(content=json.dumps(om_snippet_data), content_type='application/json')


def get_om_snippet(snippet_id):
    if int(snippet_id) == 0:
        return -1

    om_snippet_data = {}
    om_snippet = EMODSnippet.objects.get(id=snippet_id)

    om_snippet_data['name'] = om_snippet.name

    om_snippet_data['emod_snippet_id'] = om_snippet.id
    om_snippet_data['emod_snippet'] = om_snippet.snippet

    return om_snippet_data


@never_cache
@csrf_exempt
def delete_scenario(request, representative_id):
    try:
        representative_scenario = RepresentativeScenario.objects.get(id=representative_id)
        if representative_scenario.user != DimUser.objects.get_or_create(username=request.user.username)[0]:
            raise PermissionDenied
        representative_scenario.is_deleted = True
        representative_scenario.time_deleted = datetime.now()
        representative_scenario.save()
        set_notification('alert-success', '<strong>Success!</strong> Successfully deleted.', request.session)
    except PermissionDenied:
        raise PermissionDenied
    except:
        set_notification('alert-error', '<strong>Error!</strong> Failed to delete.', request.session)

    return redirect("ts_repr.browse_scenario")