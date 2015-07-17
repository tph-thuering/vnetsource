from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from data_services.models import DimUser, SimulationInputFile
from lib.templatetags.base_extras import set_notification

from ts_repr.models import RepresentativeWeather


class ManageWeatherView(TemplateView):
    template_name = 'ts_repr/managers/manage_weather.html'

    def get_context_data(self, **kwargs):
        context = super(ManageWeatherView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'managers'
        context['current_manager'] = 'weather'
        context['weather_data_url'] = "/ts_repr/weather/data/"

        context['active_weather'] = RepresentativeWeather.objects.filter(is_active=True).order_by('id')
        context['inactive_weather'] = RepresentativeWeather.objects.filter(is_active=False).order_by('id')

        return context

    def post(self, request):
        try:
            self.create_or_update_weather_files(request)
        except Exception as exception:
            set_notification('alert-error', '<strong>Error!</strong> The entry may not have been saved! ' + str(exception), self.request.session)

        return HttpResponseRedirect(reverse('ts_repr.manage_weather'))

    def create_or_update_weather_files(self, request):
        username = "khostetl"
        metadata = {}

        weather_id = int(request.POST['weather_id'])
        name = request.POST['name']
        description = request.POST['description']

        if 'is_active' in request.POST:
            is_active = True
        else:
            is_active = False

        if 'rainfall_json' in request.FILES \
            and 'rainfall_bin' in request.FILES \
            and 'humidity_json' in request.FILES \
            and 'humidity_bin' in request.FILES \
            and 'temperature_json' in request.FILES \
            and 'temperature_bin' in request.FILES:
                are_files_here = True
        else:
            are_files_here = False

        if 'rainfall_file_location' in request.POST:
            rainfall_file_location = request.POST['rainfall_file_location']
        else:
            rainfall_file_location = ''

        if 'humidity_file_location' in request.POST:
            humidity_file_location = request.POST['humidity_file_location']
        else:
            humidity_file_location = ''

        if 'temperature_file_location' in request.POST:
            temperature_file_location = request.POST['temperature_file_location']
        else:
            temperature_file_location = ''

        # 0 means we are explicitly requesting a new object, else we are looking for a specific one that supposedly
        # already exists, but if it doesn't, it will be created anyway
        if weather_id == 0:
            weather = RepresentativeWeather.objects.create(name=name,
                                            short_description='a',
                                            description=description,
                                            is_active=is_active,
                                            emod_weather_rainfall_file_location=rainfall_file_location,
                                            emod_weather_humidity_file_location=humidity_file_location,
                                            emod_weather_temperature_file_location=temperature_file_location)
        else:
            try:  # Does exist, so modify with values from above
                weather = RepresentativeWeather.objects.get(id=weather_id)
                weather.name = name
                weather.description = description
                weather.is_active = is_active
                weather.emod_weather_rainfall_file_location = rainfall_file_location
                weather.emod_weather_humidity_file_location = humidity_file_location
                weather.emod_weather_temperature_file_location = temperature_file_location
            except:  # Doesn't exist, so fill in with values from above
                weather = RepresentativeWeather.objects.create(name=name,
                                                short_description='a',
                                                description=description,
                                                is_active=is_active,
                                                emod_weather_rainfall_file_location=rainfall_file_location,
                                                emod_weather_humidity_file_location=humidity_file_location,
                                                emod_weather_temperature_file_location=temperature_file_location)

        # File names to be used.
        rainfall_json_file_name_short = "rainfall.json"
        rainfall_bin_file_name_short = "rainfall.json.bin"
        humidity_json_file_name_short = "humidity.json"
        humidity_bin_file_name_short = "humidity.json.bin"
        temperature_json_file_name_short = "temperature.json"
        temperature_bin_file_name_short = "temperature.json.bin"

        if are_files_here:
            # Grab the contents from said files
            rainfall_json_file_contents = request.FILES['rainfall_json'].read()
            rainfall_bin_file_contents = request.FILES['rainfall_bin'].read()
            humidity_json_file_contents = request.FILES['humidity_json'].read()
            humidity_bin_file_contents = request.FILES['humidity_bin'].read()
            temperature_json_file_contents = request.FILES['temperature_json'].read()
            temperature_bin_file_contents = request.FILES['temperature_bin'].read()

            # Create the simulation input files of these weather files.
            rainfall_json_simulation_file = SimulationInputFile.objects.create_file(
                contents=rainfall_json_file_contents,
                name=rainfall_json_file_name_short,
                metadata=metadata,
                created_by=DimUser.objects.get(username=username)
            )

            rainfall_bin_simulation_file = SimulationInputFile.objects.create_file(
                contents=rainfall_bin_file_contents,
                name=rainfall_bin_file_name_short,
                metadata=metadata,
                created_by=DimUser.objects.get(username=username)
            )

            humidity_json_simulation_file = SimulationInputFile.objects.create_file(
                contents=humidity_json_file_contents,
                name=humidity_json_file_name_short,
                metadata=metadata,
                created_by=DimUser.objects.get(username=username)
            )

            humidity_bin_simulation_file = SimulationInputFile.objects.create_file(
                contents=humidity_bin_file_contents,
                name=humidity_bin_file_name_short,
                metadata=metadata,
                created_by=DimUser.objects.get(username=username)
            )

            temperature_json_simulation_file = SimulationInputFile.objects.create_file(
                contents=temperature_json_file_contents,
                name=temperature_json_file_name_short,
                metadata=metadata,
                created_by=DimUser.objects.get(username=username)
            )

            temperature_bin_simulation_file = SimulationInputFile.objects.create_file(
                contents=temperature_bin_file_contents,
                name=temperature_bin_file_name_short,
                metadata=metadata,
                created_by=DimUser.objects.get(username=username)
            )

            # Save the simulation input files
            rainfall_json_simulation_file.save()
            rainfall_bin_simulation_file.save()
            humidity_json_simulation_file.save()
            humidity_bin_simulation_file.save()
            temperature_json_simulation_file.save()
            temperature_bin_simulation_file.save()

            # Remove old files if they exist
            if weather.emod_weather is not None:
                for weather_file in weather.emod_weather.all():
                    weather.emod_weather.remove(weather_file)

            # Add all the files to the table
            weather.emod_weather.add(rainfall_json_simulation_file)
            weather.emod_weather.add(rainfall_bin_simulation_file)
            weather.emod_weather.add(humidity_json_simulation_file)
            weather.emod_weather.add(humidity_bin_simulation_file)
            weather.emod_weather.add(temperature_json_simulation_file)
            weather.emod_weather.add(temperature_bin_simulation_file)

        weather.save()
        set_notification('alert-success', '<strong>Success!</strong> Successfully saved.', self.request.session)