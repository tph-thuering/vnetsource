import ast
import copy
import datetime
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
import requests
from VECNet.settings import ROOT_URLCONF
from change_doc import Change, JCD
from data_services.adapters import EMOD_Adapter
from data_services.data_api import EMODBaseline

from data_services.models import DimUser, DimBaseline
from data_services.views.misc_functions import send_calibration_request
from job_services.dispatcher import submit
from lib.templatetags.base_extras import set_notification
from ts_repr.calib import get_calibrated_species

from ts_repr.models import RepresentativeWeather, RepresentativeDemographics, \
    RepresentativeSpecies

import json
from ts_repr.utils.misc_functions import get_species_data, DETAILS_STEP
from ts_repr.views.creation.ParasiteView import get_parasite_parameters

step_number = DETAILS_STEP


class DetailsView(TemplateView):
    template_name = 'ts_repr/creation/details.html'

    def get_context_data(self, **kwargs):
        context = super(DetailsView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'new_scenario'
        context['current_step'] = 'details'
        context['weather_base_url'] = "/ts_repr/weather/data/"
        context['demographics_base_url'] = "/ts_repr/demographics/data/"
        context['details_save_url'] = '/ts_repr/details/save_data/'
        context['debug_mode'] = False

        # Retrieve all saved data from the RepresentativeScenario
        scenario = DimBaseline.objects.get(id=kwargs['scenario_id'])
        context['scenario'] = scenario

        if scenario.user != DimUser.objects.get_or_create(username=self.request.user.username)[0]:
            raise PermissionDenied

        if scenario.name == '':
            context['scenario_name'] = derive_autoname(scenario)
        else:
            context['scenario_name'] = scenario.name

        current_metadata = json.loads(scenario.metadata)

        context['weather_id'] = current_metadata['representative']['weather_id']
        context['weather_name'] = get_weather_name(current_metadata['representative']['weather_id'])
        context['demographics_id'] = current_metadata['representative']['demographics_id']
        context['demographics_name'] = get_demographics_name(current_metadata['representative']['demographics_id'])
        context['species'] = self.get_species(current_metadata['representative']['species'])
        # if 'parasite_parameters' in current_metadata['representative']:
        #     context['parasite_parameters'] = current_metadata['representative']['parasite_parameters']
        #     print context['parasite_parameters']
        # else:
        #     print current_metadata
        context['parasite_parameters'] = get_parasite_parameters(scenario.id)
        print "details page = " + str(context['parasite_parameters'])

        context['scenario_steps_complete'] = current_metadata['representative']['steps_complete']
        context['scenario_is_editable'] = current_metadata['representative']['is_editable']

        return context

    def post(self, request, scenario_id):
        save_scenario_name(request, scenario_id, request.POST['scenario_name'])

        if 'pre-calibration' in request.POST:
            use_precalibrated_values(scenario_id)
            submit_a_verification_job(request, scenario_id)
        elif 'calibrate' in request.POST:
            targets = get_targets(request, scenario_id)
            send_calibration_request(request, targets, scenario_id)

        return HttpResponseRedirect(reverse("ts_emod_scenario_details", kwargs={'scenario_id': scenario_id}))

    def get_species(self, species_json):
        print species_json
        return self.temp_get_species(species_json)  # Temporary skip of parameters gathering

        # Add information that isn't stored in the json. This will allow the backend to load up this information in
        # a nice and easy way before it hands it off to the frontend. This way the frontend won't have to make extra
        # calls back to the backend for the missing information.
        # for species in species_json:
        #     representative_species = RepresentativeSpecies.objects.get(id=species['species_id'])
        #     species['name'] = representative_species.name
        #
        #     for parameter in species['parameters']:
        #         representative_parameter = RepresentativeSpeciesParameter.objects.get(id=parameter['id'])
        #         parameter['name'] = representative_parameter.name
        #         parameter['emod_value'] = self.get_parameter_value(parameter['choice'], representative_parameter, 'emod')
        #         parameter['om_value'] = self.get_parameter_value(parameter['choice'], representative_parameter, 'om')

    def temp_get_species(self, species_json):
        new_species_json = []

        for species in species_json:
            representative_species = RepresentativeSpecies.objects.get(id=species['species_id'])
            species = get_species_data(species['species_id'])
            species['pretty_name'] = representative_species.name
            new_species_json.append(species)

        return new_species_json

    def get_parameter_value(self, choice, parameter, model):
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


def derive_autoname(scenario):
    current_metadata = json.loads(scenario.metadata)

    name = ""
    if 'weather_id' in current_metadata['representative']:
        name += get_weather_name(current_metadata['representative']['weather_id']) + "-"

        if 'demographics_id' in current_metadata['representative']:
            name += get_demographics_name(current_metadata['representative']['demographics_id']) + "-"

            if 'species' in current_metadata['representative']:
                for species in current_metadata['representative']['species']:
                    name += get_species_name(species['species_id']) + "-"

                name = name[:-1]  # Remove the extra -

    else:
        name = "New Representative Simulation"

    return name


def get_weather_name(weather_id):
    weather = RepresentativeWeather.objects.get(id=weather_id)
    return weather.name


def get_demographics_name(demographics_id):
    demographics = RepresentativeDemographics.objects.get(id=demographics_id)
    return demographics.name


def get_species_name(species_id):
    species = RepresentativeSpecies.objects.get(id=species_id)
    return species.name


def get_targets(request, scenario_id):
    dim_scenario = DimBaseline.objects.get(id=scenario_id)

    # Check to see if this user has permission
    if dim_scenario.user != DimUser.objects.get_or_create(username=request.user.username)[0]:
        raise PermissionDenied

    # Hack until I know how to retrieve files from DimBaseline without funneling it through EMODBaseline
    emod_scenario = EMODBaseline.from_dw(id=scenario_id)

    # Populate config
    config_json = json.loads(emod_scenario.get_config_file().content)

    # Get species
    species = config_json['parameters']['Vector_Species_Params']
    print species

    # Get EIR
    current_metadata = json.loads(dim_scenario.metadata)
    if 'parasite_parameters' in current_metadata['representative']:
        eir = current_metadata['representative']['parasite_parameters']['EIR']
    else:
        raise Exception("parasite_parameters missing from metadata.")
    print eir

    # Set up the targets dictionary with the items we want
    targets = {}
    targets['sporozoite'] = []
    targets['eir'] = []

    for specie in species:
        targets['sporozoite'].append(species[specie]['Sporozoite_Rate'])
        targets['eir'].append(eir)

    return targets


def get_weather_precalibration_name(weather_id):
    weather = RepresentativeWeather.objects.get(id=weather_id)
    return weather.precalibration_name


def get_demographics_precalibration_name(demographics_id):
    demographics = RepresentativeDemographics.objects.get(id=demographics_id)
    return demographics.precalibration_name


def use_precalibrated_values(scenario_id):
    emod_scenario = EMODBaseline.from_dw(id=scenario_id)
    dim_scenario = DimBaseline.objects.get(id=scenario_id)
    current_metadata = json.loads(dim_scenario.metadata)

    weather_id = current_metadata['representative']['weather_id']
    demographics_id = current_metadata['representative']['demographics_id']

    weather_precalibration_name = get_weather_precalibration_name(weather_id)
    demographics_precalibration_name = get_demographics_precalibration_name(demographics_id)

    # Populate config
    config_json = json.loads(emod_scenario.get_config_file().content)
    vector_species_parameters = config_json['parameters']['Vector_Species_Params']

    print vector_species_parameters

    for species in vector_species_parameters:
        eir = int(vector_species_parameters[species]['EIR'])
        new_species_parameters = json.loads(get_calibrated_species(weather_precalibration_name, demographics_precalibration_name, eir, species))
        vector_species_parameters[species] = new_species_parameters

    emod_scenario.add_file_from_string('config', 'config.json', json.dumps(config_json), description='SOMETHING')
    print config_json


def submit_a_verification_job(request, scenario_id):
    adapter = EMOD_Adapter(request.user.username)

    emod_scenario = EMODBaseline.from_dw(id=scenario_id)
    config_json = ast.literal_eval(emod_scenario.get_file_by_type('config').content)

    config_json['parameters']['Simulation_Duration'] = 20 * 365  # 20 years
    emod_scenario.add_file_from_string('config', 'config.json', json.dumps(config_json), description='SOMETHING')

    my_simulation_duration = config_json['parameters']['Simulation_Duration']

    ## Set the run start_date based on location and config's start_time
    my_start_date = \
        datetime.datetime.strptime(emod_scenario.template.climate_start_date, '%Y-%m-%d').date() \
            + datetime.timedelta(days=config_json['parameters']['Start_Time'])

    # Initialize the run
    run = adapter.save_run(scenario_id=scenario_id,
                              template_id=int(emod_scenario.template.id),
                              start_date=my_start_date,
                              duration=my_simulation_duration,
                              name='calibration-verification',
                              description=str(datetime.datetime.now()),
                              location_ndx=emod_scenario.template.location_key.id,
                              timestep_interval=1,
                              run_id=-1,
                              as_object=True)

    run.baseline_key_id = scenario_id
    run.save()

    # add in JCD for config file
    changes = []
    newdict = copy.deepcopy(config_json)

    newdict['config.json/parameters'] = newdict.pop('parameters')
    changes.append(Change.node(name='config.json', node=[newdict], mode='-'))

    run.jcd = JCD.from_changes(changes)
    run.save()

    ### Launch the run

    # 5853 - hard-code to 1 for now
    #reps_per_exec = int(self.get_cleaned_data_for_step('start')['reps_per_exec'])
    reps_per_exec = 1

    # submit returns tuple (success, message)
    try:
        status = submit(run, user=request.user, manifest=True, reps_per_exec=reps_per_exec)

        set_notification('alert-success', '<strong>Success!</strong> Run launched.', request.session)
    except (RuntimeError, TypeError, AssertionError), e:
        set_notification('alert-error', '<strong>Error!</strong> ' + str(e.message), request.session)

    dim_scenario = DimBaseline.objects.get(id=scenario_id)
    current_metadata = json.loads(dim_scenario.metadata)
    current_metadata['calibration_verification_run_id'] = run.id
    dim_scenario.metadata = json.dumps(current_metadata)
    dim_scenario.save()


def save_scenario_name(request, scenario_id, scenario_name):
    scenario = DimBaseline.objects.get(id=scenario_id)

    # Check to see if this user has permission
    if scenario.user != DimUser.objects.get_or_create(username=request.user.username)[0]:
        raise PermissionDenied

    # Print data
    print "Scenario name = " + scenario_name

    # Fill data
    scenario.name = scenario_name

    scenario.save()

    set_notification('alert-success', '<strong>Success!</strong> Successfully updated simulation name.', request.session)


@csrf_exempt
def save_scenario_name_ajax(request):
    data = json.loads(request.body)
    save_scenario_name(request, data['scenario_id'], data['scenario_name'])

    return HttpResponse()