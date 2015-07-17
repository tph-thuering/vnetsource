from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from data_services.data_api import EMODBaseline

from data_services.models import DimUser, DimBaseline

from ts_repr.models import RepresentativeSpecies

import json
from ts_repr.utils.misc_functions import get_species, get_species_data, SPECIES_STEP

step_number = SPECIES_STEP


class SpeciesView(TemplateView):
    template_name = 'ts_repr/creation/species.html'

    def get_context_data(self, **kwargs):
        context = super(SpeciesView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'new_scenario'
        context['current_step'] = 'species'
        context['page_name'] = 'species'
        context['species_data_url'] = "/ts_repr/species/data/"

        scenario = DimBaseline.objects.get(id=kwargs['scenario_id'])
        context['scenario'] = scenario

        if scenario.user != DimUser.objects.get_or_create(username=self.request.user.username)[0]:
            raise PermissionDenied

        context['species_options'] = self.get_species_options()

        current_metadata = json.loads(scenario.metadata)

        context['scenario_steps_complete'] = current_metadata['representative']['steps_complete']
        context['scenario_is_editable'] = current_metadata['representative']['is_editable']

        if current_metadata['representative']['steps_complete'] > step_number:
            context['can_use_just_save'] = True
        else:
            context['can_use_just_save'] = False

        # Prepopulate if there are already choices
        context['previously_selected_species_ids'] = self.get_species_ids(scenario)

        return context

    def post(self, request, scenario_id):
        #return HttpResponseRedirect(reverse('ts_repr.details', kwargs={'scenario_id': scenario_id}))
        return HttpResponseRedirect(reverse('ts_repr.parasite', kwargs={'scenario_id': scenario_id}))

    def get_species_options(self):
        species = RepresentativeSpecies.objects.filter(is_active=True)
        species_options_unsorted = []

        for specie in species:
            species_options_unsorted.append({'name': str(specie.name), 'id': specie.id})

        # Sort list based on name
        species_options_sorted = sorted(species_options_unsorted, key=lambda species_name: species_name['name'])

        return species_options_sorted

    def get_species_ids(self, scenario):
        species_ids = []

        metadata = json.loads(scenario.metadata)
        representative_data = metadata['representative']

        if 'species' in representative_data:
            species = representative_data['species']

            for i in range(len(species)):  # Get each species ids
                species_ids.append(int(species[i]['species_id']))

        return species_ids


@never_cache
@csrf_exempt
def get_species_data_ajax(request, option_id):
    species_data = get_species_data(option_id)

    return HttpResponse(content=json.dumps(species_data), content_type='application/json')


@csrf_exempt
def save_species_data(request):
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
    print "Data = " + str(data)

    # Fill data
    if current_metadata['representative']['steps_complete'] <= step_number:
        current_metadata['representative']['steps_complete'] = step_number + 1
    current_metadata['representative']['species'] = data['species']
    dim_scenario.metadata = json.dumps(current_metadata)

    dim_scenario.save()

    # Hack until I know how to retrieve files from DimBaseline without funneling it through EMODBaseline
    emod_scenario = EMODBaseline.from_dw(id=data['scenario_id'])

# Add the species to the scenario
    # Load species data
    species = get_species(data['species'])

    # Populate config
    config_json = json.loads(emod_scenario.get_config_file().content)
    print config_json

    # Change config
    for i in range(len(species)):
        species_name = species[i].emod_snippet.name
        config_json['parameters']['Vector_Species_Names'].append(species_name)
        config_json['parameters']['Vector_Species_Params'][species_name] = json.loads(species[i].emod_snippet.snippet)[species_name]

    print config_json

    # Attach the scenario's config file
    emod_scenario.add_file_from_string('config', 'config.json', json.dumps(config_json), description='SOMETHING')

    emod_scenario.save()

    return HttpResponse()