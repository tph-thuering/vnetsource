from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from data_services.data_api import EMODBaseline

from data_services.models import DimUser, DimBaseline

from ts_repr.models import RepresentativeDemographics
from ts_repr.utils.misc_functions import get_demographics, DEMOGRAPHICS_STEP

import json

step_number = DEMOGRAPHICS_STEP


class DemographicsView(TemplateView):
    template_name = 'ts_repr/creation/demographics.html'

    def get_context_data(self, **kwargs):
        context = super(DemographicsView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'new_scenario'
        context['current_step'] = 'demographics'
        context['page_name'] = 'demographics'
        context['demographics_data_url'] = "/ts_repr/demographics/data/"

        scenario = DimBaseline.objects.get(id=kwargs['scenario_id'])
        context['scenario'] = scenario

        if scenario.user != DimUser.objects.get_or_create(username=self.request.user.username)[0]:
            raise PermissionDenied

        context['demographics_options'] = self.get_demographics_options()

        current_metadata = json.loads(scenario.metadata)
        print current_metadata

        context['scenario_steps_complete'] = current_metadata['representative']['steps_complete']
        context['scenario_is_editable'] = current_metadata['representative']['is_editable']

        if current_metadata['representative']['steps_complete'] > step_number:
            context['can_use_just_save'] = True
        else:
            context['can_use_just_save'] = False

        # Prepopulate if there is already a choice
        context['demographics_id'] = self.get_demographics_id(scenario)
        
        return context

    def post(self, request, scenario_id):
        return HttpResponseRedirect(reverse('ts_repr.species', kwargs={'scenario_id': scenario_id}))

    def get_demographics_options(self):
        demographics = RepresentativeDemographics.objects.filter(is_active=True)
        return demographics

    def get_demographics_id(self, scenario):
        # Get the metadata
        current_metadata = json.loads(scenario.metadata)

        if 'demographics_id' in current_metadata['representative']:
            demographics_id = int(current_metadata['representative']['demographics_id'])
        else:
            demographics_id = 0

        return demographics_id


@never_cache
@csrf_exempt
def get_demographics_data(request, option_id):
    # This is used in manage_demographics to allow success ajax code to be ran on "New Demographics"
    if int(option_id) == 0:
        return HttpResponse(content=json.dumps(-1))

    demographics = RepresentativeDemographics.objects.get(id=option_id)
    demographics_data = {}

    if demographics.type == "Exponential":
        categories = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105]
        quantities = [188, 151, 118, 100, 87, 66, 68, 52, 37, 34, 13, 15, 11, 18, 10, 9, 3, 4, 2, 4, 10]
        quantities = scale_quantities(quantities)  # Correction for exponential
        categories, quantities = fix_bins(categories, quantities)
        demographics_data['categories'] = categories
        demographics_data['chart_data'] = quantities
    else:
        if demographics.emod_demographics:
            demographics_contents = demographics.emod_demographics.get_contents()

            try:
                # Grab the originals from the file
                quantities = json.loads(demographics_contents)['Nodes'][0]['IndividualAttributes']['AgeDistribution']['DistributionValues']
                categories = json.loads(demographics_contents)['Nodes'][0]['IndividualAttributes']['AgeDistribution']['ResultValues']

                # Modify them to be more sensible for charts
                categories, quantities = parse_distribution_data(categories, quantities)  # Correction for non-exponential
                categories, quantities = fix_bins(categories, quantities)

                demographics_data['categories'] = categories
                demographics_data['chart_data'] = quantities
            except:
                demographics_data['categories'], demographics_data['chart_data'] = [0], [0]
        else:
            demographics_data['categories'], demographics_data['chart_data'] = [0], [0]

    # Demographics info
    demographics_data['name'] = demographics.name
    demographics_data['description'] = demographics.description
    demographics_data['type'] = demographics.type
    demographics_data['types'] = ['Exponential', 'Non-Exponential']
    demographics_data['is_active'] = demographics.is_active
    demographics_data['file_location'] = demographics.emod_demographics_compiled_file_location

    return HttpResponse(content=json.dumps(demographics_data))#, content_type='application/json')


def fix_bins(categories, quantities, desired_bin_size=5):
    CATEGORY = 0
    PERCENTAGE = 1
    fixed_age_bins = []
    bins_complete = 0
    current_fixed_bin = [desired_bin_size, 0]
    previous_bin_category = 0
    last_bin_added = True

    age_bins = form_bins(categories, quantities)

    for age_bin in age_bins:
        current_bin = age_bin

        while True:
            bin_size_needed = desired_bin_size * (bins_complete + 1) - current_bin[CATEGORY]

            if bin_size_needed > 0:  # Still need more bins to fill this fixed_bin
                current_fixed_bin[PERCENTAGE] += current_bin[PERCENTAGE]
                previous_bin_category = current_bin[CATEGORY]
                last_bin_added = False
                break  # current_bin is depleted, move to next bin
            elif bin_size_needed == 0:  # Got just enough for this bin
                current_fixed_bin[PERCENTAGE] += current_bin[PERCENTAGE]
                bins_complete += 1  # We filled another fixed_age_bin
                fixed_age_bins.append(current_fixed_bin)  # Add the bin
                current_fixed_bin = [current_fixed_bin[CATEGORY] + desired_bin_size, 0]  # Reset for next bin
                previous_bin_category = current_bin[CATEGORY]
                last_bin_added = True
                break  # current_bin is depleted, move to next bin
            else:  # Is negative so we got more than enough and we only want part of it, such that it is proportionate.
                interval_size = previous_bin_category - current_bin[CATEGORY]
                percent_needed = 1 - (float(bin_size_needed) / float(interval_size))  # bin_size_needed in this case is extra
                current_fixed_bin[PERCENTAGE] += current_bin[PERCENTAGE] * percent_needed  # Take only enough to fill the bin
                bins_complete += 1  # We filled another fixed_age_bin
                previous_bin_category = current_fixed_bin[CATEGORY]
                fixed_age_bins.append(current_fixed_bin)  # Add the bin
                current_fixed_bin = [current_fixed_bin[CATEGORY] + desired_bin_size, 0]  # Reset for next bin
                left_over_from_bin = current_bin[PERCENTAGE] * (1 - percent_needed)  # This will be applied to the next bin
                current_bin = [current_bin[CATEGORY], left_over_from_bin]  # current_bin still has some left so use it again
                last_bin_added = True

    if not last_bin_added:
        fixed_age_bins.append(current_fixed_bin)  # Add the bin

    return deform_bins(fixed_age_bins)


def parse_distribution_data(categories, quantities):
    correct_categories = categories[1:]  # Remove the first entry since it is useless. It is just 0 and is not used.
    quantities1 = quantities[:-1]
    quantities2 = quantities[1:]
    correct_quantities = []

    for i in range(len(quantities1)):
        correct_quantities.append(quantities2[i] - quantities1[i])

    return correct_categories, correct_quantities


def form_bins(categories, quantities):
    age_bins = []

    for i in range(len(categories)):
        age_bins.append([categories[i], quantities[i]])

    return age_bins


def deform_bins(age_bins):
    categories = []
    quantities = []
    CATEGORY = 0
    VALUE = 1

    for i in range(len(age_bins)):
        categories.append(age_bins[i][CATEGORY])
        quantities.append([i, age_bins[i][VALUE] * 100])  # fixthis this should not multiply by 100 unless it is fractions

    return categories, quantities


def scale_quantities(quantities):
    total = sum(quantities)
    new_quantities = []

    for i in range(len(quantities)):
        new_quantities.append(float(quantities[i]) / float(total))

    return new_quantities


@csrf_exempt
def save_demographics_data(request):
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
    print "Demographics id = " + data['demographics_id']

    # Fill data
    if current_metadata['representative']['steps_complete'] <= step_number:
        current_metadata['representative']['steps_complete'] = step_number + 1
    current_metadata['representative']['demographics_id'] = data['demographics_id']
    dim_scenario.metadata = json.dumps(current_metadata)

    dim_scenario.save()

    # Hack until I know how to retrieve files from DimBaseline without funneling it through EMODBaseline
    emod_scenario = EMODBaseline.from_dw(id=data['scenario_id'])

# Add the demographics to the scenario
    # Load demographics data
    demographics_data = get_demographics(data['demographics_id'])

    # Populate config
    config_json = json.loads(emod_scenario.get_config_file().content)
    print config_json

    # Change config
    config_json['parameters']['Demographics_Filename'] = demographics_data['file_location']

    # Attach the scenario's config file
    emod_scenario.add_file_from_string('config', 'config.json', json.dumps(config_json), description='SOMETHING')

    # Add the demographics
    emod_scenario.add_file_from_string('demographics', 'demographics.compiled.json', demographics_data['file_data'], description='SOMETHING')

    emod_scenario.save()

    return HttpResponse()