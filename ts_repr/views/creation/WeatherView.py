from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from data_services.data_api import EMODBaseline
from data_services.models import DimUser, DimBaseline
from ts_emod2.utils.weather_chart_data import parse_weather_for_data

from ts_repr.models import RepresentativeWeather
from ts_repr.utils.misc_functions import get_weather, WEATHER_STEP

import json

step_number = WEATHER_STEP


class WeatherView(TemplateView):
    template_name = 'ts_repr/creation/weather/weather.html'

    def get_context_data(self, **kwargs):
        context = super(WeatherView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'new_scenario'
        context['current_step'] = 'weather'
        context['page_name'] = 'weather'
        context['weather_base_url'] = "/ts_repr/weather/data/"

        scenario = DimBaseline.objects.get(id=kwargs['scenario_id'])
        context['scenario'] = scenario

        if scenario.user != DimUser.objects.get_or_create(username=self.request.user.username)[0]:
            raise PermissionDenied

        context['weather_options'] = self.get_weather_options()

        if scenario.metadata:
            current_metadata = json.loads(scenario.metadata)

            context['scenario_steps_complete'] = current_metadata['representative']['steps_complete']
            context['scenario_is_editable'] = current_metadata['representative']['is_editable']

            if current_metadata['representative']['steps_complete'] > step_number:
                context['can_use_just_save'] = True
            else:
                context['can_use_just_save'] = False

            # Prepopulate if there is already a choice
            context['weather_id'] = self.get_weather_id(scenario)
        else:
            context['can_use_just_save'] = False
            context['weather_id'] = 0

        return context

    def post(self, request, scenario_id):
        return HttpResponseRedirect(reverse('ts_repr.demographics', kwargs={'scenario_id': scenario_id}))

    def get_weather_options(self):
        weather = RepresentativeWeather.objects.filter(is_active=True)
        return weather

    def get_weather_id(self, scenario):
        # Get the metadata
        current_metadata = json.loads(scenario.metadata)

        if 'weather_id' in current_metadata['representative']:
            weather_id = int(current_metadata['representative']['weather_id'])
        else:
            weather_id = 0

        return weather_id


@never_cache
@csrf_exempt
def get_weather_data(request, option_id):
    # This is used in manage_weather to allow success ajax code to be ran on "New Weather"
    if int(option_id) == 0:
        return HttpResponse(content=json.dumps(-1))

    weather = RepresentativeWeather.objects.get(id=option_id)
    weather_data = {}

    if len(weather.emod_weather.all()) == 6:  # 6 files: 3 bins and 3 jsons
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

        # Actual chart data
        weather_data['rainfall'] = parse_weather_for_data(rainfall_json, rainfall_bin)
        weather_data['humidity'] = parse_weather_for_data(humidity_json, humidity_bin)
        weather_data['temperature'] = parse_weather_for_data(temperature_json, temperature_bin)
    else:  # Else we are missing files
        weather_data['rainfall'] = []
        weather_data['humidity'] = []
        weather_data['temperature'] = []

    # Weather info
    weather_data['name'] = weather.name
    weather_data['description'] = weather.description
    print weather.description
    weather_data['is_active'] = weather.is_active
    weather_data['file_locations'] = {}
    weather_data['file_locations']['rainfall'] = weather.emod_weather_rainfall_file_location
    weather_data['file_locations']['humidity'] = weather.emod_weather_humidity_file_location
    weather_data['file_locations']['temperature'] = weather.emod_weather_temperature_file_location

    return HttpResponse(content=json.dumps(weather_data)) #, content_type='application/json')


@csrf_exempt
def save_weather_data(request):
    # Get data
    data = json.loads(request.body)
    # Hack until I know how to retrieve files from DimBaseline without funneling it through EMODBaseline
    dim_scenario = DimBaseline.objects.get(id=data['scenario_id'])

    # Check to see if this user has permission
    if dim_scenario.user != DimUser.objects.get_or_create(username=request.user.username)[0]:
        raise PermissionDenied

    # Get the metadata
    current_metadata = json.loads(dim_scenario.metadata)

    # Print data
    print current_metadata
    print data
    print "Weather id = " + data['weather_id']

    # Fill data
    if current_metadata['representative']['steps_complete'] <= step_number:
        current_metadata['representative']['steps_complete'] = step_number + 1
    current_metadata['representative']['weather_id'] = data['weather_id']
    dim_scenario.metadata = json.dumps(current_metadata)

    print dim_scenario.metadata

    dim_scenario.save()

    # Hack until I know how to retrieve files from DimBaseline without funneling it through EMODBaseline
    emod_scenario = EMODBaseline.from_dw(id=data['scenario_id'])

# Add the weather to the scenario
    # Load weather data
    weather_data = get_weather(data['weather_id'])

    # Populate config
    config_json = json.loads(emod_scenario.get_config_file().content)
    print config_json

    # Change config
    config_json['parameters']['Rainfall_Filename'] = weather_data['file_locations']['rainfall']
    config_json['parameters']['Relative_Humidity_Filename'] = weather_data['file_locations']['humidity']
    config_json['parameters']['Air_Temperature_Filename'] = weather_data['file_locations']['temperature']
    config_json['parameters']['Land_Temperature_Filename'] = weather_data['file_locations']['temperature']

    # Attach the emod_scenario config file
    emod_scenario.add_file_from_string('config', 'config.json', json.dumps(config_json), description='SOMETHING')

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

    emod_scenario.save()

    print dim_scenario.metadata

    return HttpResponse()