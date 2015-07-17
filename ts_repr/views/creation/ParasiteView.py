from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from data_services.data_api import EMODBaseline

from data_services.models import DimUser, DimBaseline

from ts_repr.utils.misc_functions import PARASITE_STEP

import json

step_number = PARASITE_STEP


class ParasiteView(TemplateView):
    template_name = 'ts_repr/creation/parasite.html'

    def get_context_data(self, **kwargs):
        context = super(ParasiteView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'new_scenario'
        context['current_step'] = 'parasite'
        context['page_name'] = 'parasite'

        scenario = DimBaseline.objects.get(id=kwargs['scenario_id'])
        context['scenario'] = scenario

        if scenario.user != DimUser.objects.get_or_create(username=self.request.user.username)[0]:
            raise PermissionDenied

        context['parasite_parameters'] = get_parasite_parameters(scenario.id)

        print "parasite page = " + str(context['parasite_parameters'])

        current_metadata = json.loads(scenario.metadata)

        context['scenario_steps_complete'] = current_metadata['representative']['steps_complete']
        context['scenario_is_editable'] = current_metadata['representative']['is_editable']

        if current_metadata['representative']['steps_complete'] > step_number:
            context['can_use_just_save'] = True
        else:
            context['can_use_just_save'] = False
        
        return context

    def post(self, request, scenario_id):
        return HttpResponseRedirect(reverse('ts_repr.details', kwargs={'scenario_id': scenario_id}))


def get_parasite_parameters(scenario_id):
    parasite_parameters = {}
    parasite_parameters['species'] = {}

    emod_scenario = EMODBaseline.from_dw(id=scenario_id)

    # Populate config
    config_json = json.loads(emod_scenario.get_config_file().content)

    vector_species_parameters = config_json['parameters']['Vector_Species_Params']

    for species in vector_species_parameters:
        clean_species_name = str(species).replace(' ', '_')
        parasite_parameters['species'][clean_species_name] = {}

        if 'EIR' in vector_species_parameters[species]:
            parasite_parameters['species'][clean_species_name]['EIR'] = vector_species_parameters[species]['EIR']
        else:
            parasite_parameters['species'][clean_species_name]['EIR'] = 0

    return parasite_parameters

@csrf_exempt
def save_parasite_data(request):
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

    # Float correction
    for species in data['parasite_parameters']['species']:
        print species
        for parasite_parameter in data['parasite_parameters']['species'][species]:
            data['parasite_parameters']['species'][species][parasite_parameter] = float(data['parasite_parameters']['species'][species][parasite_parameter])

    # Fill data
    if current_metadata['representative']['steps_complete'] <= step_number:
        current_metadata['representative']['steps_complete'] = step_number + 1
    current_metadata['representative']['is_complete'] = True
    dim_scenario.metadata = json.dumps(current_metadata)

    dim_scenario.save()

    # Hack until I know how to retrieve files from DimBaseline without funneling it through EMODBaseline
    emod_scenario = EMODBaseline.from_dw(id=data['scenario_id'])

# Add the parasites to the scenario
    # Load parasite parameter data
    # parasite_parameters = data['parasite_parameters']
    # new_diagnostic_sensitivity = parasite_parameters['new_diagnostic_sensitivity']
    # parasite_smear_sensitivity = parasite_parameters['parasite_smear_sensitivity']

    # Populate config
    config_json = json.loads(emod_scenario.get_config_file().content)

    # Change config
    # config_json['parameters']['New_Diagnostic_Sensitivity'] = new_diagnostic_sensitivity
    # config_json['parameters']['Parasite_Smear_Sensitivity'] = parasite_smear_sensitivity
    for species in config_json['parameters']['Vector_Species_Params']:
        clean_species_name = species.replace(' ', '_')
        config_json['parameters']['Vector_Species_Params'][species]['EIR'] = data['parasite_parameters']['species'][clean_species_name]['EIR']

    # Attach the scenario's config file
    emod_scenario.add_file_from_string('config', 'config.json', json.dumps(config_json), description='SOMETHING')

    emod_scenario.save()

    return HttpResponse()