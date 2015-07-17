from django.forms.formsets import formset_factory
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.views.generic import TemplateView

from data_services.models import DimUser
from lib.templatetags.base_extras import set_notification

from ts_emod2.forms.InterventionForms import *
from ts_emod2.models import Scenario

import json
import re


intervention_name_to_name_for_url_map = {
    'Antimalarial Drug': 'AntimalarialDrug',
    'Human Host Seeking Trap': 'HumanHostSeekingTrap',
    'Insect Killing Fence': 'InsectKillingFence',
    'IRS Housing Modification': 'IRSHousingModification',
    'Larvicide': 'Larvicides',
    'Outbreak': 'Outbreak',
    'Oviposition Trap': 'OvipositionTrap',
    'RTSS Vaccine': 'RTSSVaccine',
    'Simple Bednet': 'SimpleBednet',
    'Simple Vaccine': 'SimpleVaccine',
    'Spatial Repellent': 'SpatialRepellent',
    'Spatial Repellent Housing Modification': 'SpatialRepellentHousingM',
    'Sugar Trap': 'SugarTrap'
}


class InterventionView2(TemplateView):
    template_name = 'ts_emod2/intervention/intervention.html'

    def get_context_data(self, **kwargs):
        context = super(InterventionView2, self).get_context_data(**kwargs)
        dim_user = DimUser.objects.get(username=self.request.user.username)
        context['dim_user'] = dim_user
        #context['nav_button'] = 'browse_scenario'

        scenario = Scenario.objects.get(id=kwargs['scenario_id'])

        # Check permissions
        if scenario.user != dim_user:
            raise PermissionDenied

        # # Get all of the interventions from local DB (public OR created by user)
        # for item in list(Intervention.objects.filter(Q(is_public=1) | Q(created_by=self.request.user))):
        #     interventions.append(item)

        # Get the campaign file
        campaign = json.loads(scenario.campaign_file.get_contents())

        # Ensure the campaign is valid, otherwise make it a valid empty campaign.
        if 'Events' not in campaign:
            campaign = {"Events": []}

        # Get all formsets and fill initial ones with ones already in the campaign file
        formsets = self.get_emod_formsets(campaign)

        # Make a list of templates based on the formsets. These aren't templates for the forms themselves, but instead
        # are just references to them.
        intervention_templates = []
        for i in range(len(formsets)):
            intervention_templates.append({})

            form = formsets[i].empty_form
            form_attributes = vars(form)

            intervention_templates[i]['name'] = form_attributes['fields']['name'].initial
            intervention_templates[i]['name_for_url'] = get_name_for_url(intervention_templates[i]['name'])
            intervention_templates[i]['prefix'] = formsets[i].prefix
            intervention_templates[i]['details'] = '<th>Parameter</th><th>Default Value</th>'

            # Fill the details table on the intervention page. Loop through all the fields in the form and put them
            # into a table, but skip start_day, number_of_repetitions, timesteps_between_repetitions,
            # max_number_of_distributions, demographic_coverage, and DELETE since these is not applicable information
            # to the details table. I know the format of this is confusing. Bear with it.
            for attribute_name in form_attributes['fields']:
                if attribute_name != "start_day" and attribute_name != "number_of_repetitions" and \
                   attribute_name != "timesteps_between_repetitions" and attribute_name != "max_number_of_distributions" and \
                   attribute_name != "demographic_coverage" and attribute_name != "DELETE":
                        attribute = form_attributes['fields'][attribute_name]
                        formatted_name = convert_underscore_lower_to_underscore_upper(attribute_name).replace('_', ' ')

                        non_camel_cased_value = convert_camel_case_to_human_readable(str(attribute.initial))
                        formatted_value = non_camel_cased_value.replace('_', ' ')

                        intervention_templates[i]['details'] += '<tr><td>' + formatted_name + \
                            '&nbsp&nbsp&nbsp&nbsp</td><td>' + formatted_value + '&nbsp&nbsp&nbsp&nbsp</td></tr>'

        # Get the config file
        config = json.loads(scenario.config_file.get_contents())

        # Get date info to determine the maximum allowable start_date for interventions.
        try:
            start_day_max = config['parameters']['Simulation_Duration']
        except TypeError:
            start_day_max = 2147480000  # Based on EMOD documentation

        context['start_day_max'] = start_day_max
        context['campaign'] = campaign
        context['scenario'] = scenario
        context['formsets'] = formsets
        context['intervention_templates'] = intervention_templates

        return context

    def post(self, request, scenario_id):
        dim_user = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        scenario = Scenario.objects.get(id=scenario_id)

        # Check permissions
        if scenario.user != dim_user:
            raise PermissionDenied

        campaign = {}
        campaign['Events'] = []
        campaign['Use_Defaults'] = 1
        interventions = {}

        # Loop through all of the stuff sent from the frontend.
        for key in request.POST:
            value = request.POST[key]
            # Example key: SimpleBednet-0-cost_to_consumer. The left defines the intervention_type, the middle defines
            # the index of the intervention list of this type, the right defines the field_name for the form of type
            # intervention_type. If the key is not one that we are looking for, it will fail the try-except below and
            # move to the next key (ie. __prefix__).
            split_key = key.split('-')

            # If this is a valid entry for our interventions and not things like csrf tokens, INITIAL_FORMS,
            # MAX_NUM_FORMS, etc.
            if len(split_key) == 3:
                intervention_type = split_key[0]

                try:
                    index = int(split_key[1])
                except ValueError:  # Read split_key description
                    continue

                field_name = split_key[2]

                if value == '':
                    value = 0

                if field_name == 'demographic_coverage':
                    value = float(value) / 100

                # Check if this intervention_type has already been added. If it has, then all of its intervention
                # entries has also been added. If this intervention_type is not already in the list, then we need to
                # add an entry for each intervention of this type right now.
                if intervention_type not in interventions:
                    interventions[intervention_type] = []

                    for j in range(int(request.POST[intervention_type + '-TOTAL_FORMS'])):
                        # Create a new intervention with all the necessary dictionaries and common default values
                        interventions[intervention_type].append({})
                        last = len(interventions[intervention_type]) - 1
                        intervention = interventions[intervention_type][last]

                        intervention['Event_Coordinator_Config'] = {}
                        event_coordinator_config = intervention['Event_Coordinator_Config']
                        event_coordinator_config['Intervention_Config'] = {}
                        event_coordinator_config['Intervention_Config']['class'] = intervention_type
                        event_coordinator_config['Target_Demographic'] = 'Everyone'
                        event_coordinator_config['class'] = 'StandardInterventionDistributionEventCoordinator'

                        intervention['Nodeset_Config'] = {}
                        intervention['Nodeset_Config']['class'] = 'NodeSetAll'

                        intervention['class'] = 'CampaignEvent'

                intervention = interventions[intervention_type][index]
                add_entry_to_intervention(intervention, field_name, value)

        # Compile all the interventions into a campaign
        for intervention_type in interventions:
            intervention_set = interventions[intervention_type]
            for i in range(len(intervention_set)):
                campaign['Events'].append(intervention_set[i])

        print campaign

        config = json.loads(scenario.config_file.get_contents())

        if len(campaign['Events']) > 0:
            # Enable in config
            if config['parameters']['Enable_Interventions'] == 0:
                config['parameters']['Enable_Interventions'] = 1
                scenario.set_file_by_type('config', json.dumps(config))

        # Replace campaign file
        scenario.set_file_by_type('campaign', json.dumps(campaign))

        set_notification('alert-success', '<strong>Success!</strong> The intervention(s) have been saved to ' +
                         scenario.name + '.', self.request.session)

        # Check if user wants to launch, or just save
        if 'submission_type' in request.POST:
            if request.POST['submission_type'] == 'launch':
                return redirect("ts_emod2.launch", scenario_id=scenario_id)
            elif request.POST['submission_type'] == 'save':
                return redirect("ts_emod2.details", scenario_id=scenario_id)
            else:
                raise Exception("Bad submission_type of " + str(request.POST['submission_type']))
        else:
            return redirect("ts_emod2.details", scenario_id=scenario_id)

    def get_emod_formsets(self, campaign):
        antimalarial_drug_interventions = []
        human_host_seeking_trap_interventions = []
        insect_killing_fence_interventions = []
        irs_housing_modification_interventions = []
        larvicide_interventions = []
        outbreak_interventions = []
        oviposition_trap_interventions = []
        rtss_vaccine_interventions = []
        simple_bednet_interventions = []
        simple_vaccine_interventions = []
        spatial_repellent_interventions = []
        spatial_repellent_housing_modification_interventions = []
        sugar_trap_interventions = []

        # Get current interventions
        for i in range(len(campaign['Events'])):
            event = campaign['Events'][i]

            # If this is a valid intervention, then get the type
            try:
                intervention_config = event['Event_Coordinator_Config']['Intervention_Config']
                intervention_type = intervention_config['class']
            except KeyError:
                print "Event = " + str(event)
                continue

            intervention = get_base_intervention(event)

            # intervention.update(get_***_intervention(intervention_config)) means to take the base intervention and
            # add the stuff specific to the intervention_type
            if intervention_type == 'AntimalarialDrug':
                parameter_map = get_parameter_map(AntimalarialDrugForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                antimalarial_drug_interventions.append(intervention)

            elif intervention_type == 'HumanHostSeekingTrap':
                parameter_map = get_parameter_map(HumanHostSeekingTrapForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                human_host_seeking_trap_interventions.append(intervention)

            elif intervention_type == 'InsectKillingFence':
                parameter_map = get_parameter_map(InsectKillingFenceForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                insect_killing_fence_interventions.append(intervention)

            elif intervention_type == 'IRSHousingModification':
                parameter_map = get_parameter_map(IRSHousingModificationForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                irs_housing_modification_interventions.append(intervention)

            elif intervention_type == 'Larvicides':
                parameter_map = get_parameter_map(LarvicideForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                larvicide_interventions.append(intervention)

            elif intervention_type == 'Outbreak':
                parameter_map = get_parameter_map(OutbreakForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                outbreak_interventions.append(intervention)

            elif intervention_type == 'OvipositionTrap':
                parameter_map = get_parameter_map(OvipositionTrapForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                oviposition_trap_interventions.append(intervention)

            elif intervention_type == 'RTSSVaccine':
                parameter_map = get_parameter_map(RTSSVaccineForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                rtss_vaccine_interventions.append(intervention)

            elif intervention_type == 'SimpleBednet':
                parameter_map = get_parameter_map(SimpleBednetForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                simple_bednet_interventions.append(intervention)

            elif intervention_type == 'SimpleVaccine':
                parameter_map = get_parameter_map(SimpleVaccineForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                simple_vaccine_interventions.append(intervention)

            elif intervention_type == 'SpatialRepellent':
                parameter_map = get_parameter_map(SpatialRepellentForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                spatial_repellent_interventions.append(intervention)

            elif intervention_type == 'SpatialRepellentHousingModification':
                parameter_map = get_parameter_map(SpatialRepellentHousingModificationForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                spatial_repellent_housing_modification_interventions.append(intervention)

            elif intervention_type == 'SugarTrap':
                parameter_map = get_parameter_map(SugarTrapForm)
                intervention.update(get_specific_intervention(intervention_config, parameter_map))
                sugar_trap_interventions.append(intervention)

            else:
                raise ValueError('Invalid intervention type')

        # Create form factories
        AntimalarialDrugFormSet = formset_factory(AntimalarialDrugForm, extra=0, can_delete=True)
        HumanHostSeekingTrapFormSet = formset_factory(HumanHostSeekingTrapForm, extra=0, can_delete=True)
        InsectKillingFenceFormSet = formset_factory(InsectKillingFenceForm, extra=0, can_delete=True)
        IRSHousingModificationFormSet = formset_factory(IRSHousingModificationForm, extra=0, can_delete=True)
        LarvicideFormSet = formset_factory(LarvicideForm, extra=0, can_delete=True)
        OutbreakFormSet = formset_factory(OutbreakForm, extra=0, can_delete=True)
        OvipositionTrapFormSet = formset_factory(OvipositionTrapForm, extra=0, can_delete=True)
        RTSSVaccineFormSet = formset_factory(RTSSVaccineForm, extra=0, can_delete=True)
        SimpleBednetFormSet = formset_factory(SimpleBednetForm, extra=0, can_delete=True)
        SimpleVaccineFormSet = formset_factory(SimpleVaccineForm, extra=0, can_delete=True)
        SpatialRepellentFormSet = formset_factory(SpatialRepellentForm, extra=0, can_delete=True)
        SpatialRepellentHousingModificationFormSet = formset_factory(SpatialRepellentHousingModificationForm, extra=0, can_delete=True)
        SugarTrapFormSet = formset_factory(SugarTrapForm, extra=0, can_delete=True)

        # Create formsets
        formsets = [AntimalarialDrugFormSet(initial=antimalarial_drug_interventions, prefix='AntimalarialDrug'),
                    HumanHostSeekingTrapFormSet(initial=human_host_seeking_trap_interventions, prefix='HumanHostSeekingTrap'),
                    InsectKillingFenceFormSet(initial=insect_killing_fence_interventions, prefix='InsectKillingFence'),
                    IRSHousingModificationFormSet(initial=irs_housing_modification_interventions, prefix='IRSHousingModification'),
                    LarvicideFormSet(initial=larvicide_interventions, prefix='Larvicides'),
                    OutbreakFormSet(initial=outbreak_interventions, prefix='Outbreak'),
                    OvipositionTrapFormSet(initial=oviposition_trap_interventions, prefix='OvipositionTrap'),
                    RTSSVaccineFormSet(initial=rtss_vaccine_interventions, prefix='RTSSVaccine'),
                    SimpleBednetFormSet(initial=simple_bednet_interventions, prefix='SimpleBednet'),
                    SimpleVaccineFormSet(initial=simple_vaccine_interventions, prefix='SimpleVaccine'),
                    SpatialRepellentFormSet(initial=spatial_repellent_interventions, prefix='SpatialRepellent'),
                    SpatialRepellentHousingModificationFormSet(initial=spatial_repellent_housing_modification_interventions, prefix='SpatialRepellentHousingModification'),
                    SugarTrapFormSet(initial=sugar_trap_interventions, prefix='SugarTrap')]

        return formsets


def get_base_intervention(event):
    intervention = {}
    intervention['start_day'] = event['Start_Day']
    event_config = event['Event_Coordinator_Config']

    if 'Number Repetitions' in event_config:
        intervention['number_of_repetitions'] = event_config['Number_Repetitions']
    if 'Timesteps_Between_Repetitions' in event_config:
        intervention['timesteps_between_repetitions'] = event_config['Timesteps_Between_Repetitions']
    if 'Number_Distributions' in event_config:
        intervention['max_number_of_distributions'] = event_config['Number_Distributions']
    if 'Demographic_Coverage' in event_config:
        intervention['demographic_coverage'] = event_config['Demographic_Coverage'] * 100

    return intervention


def get_specific_intervention(intervention_config, parameter_map):
    intervention = {}

    for parameter in parameter_map:
        campaign_parameter = parameter_map[parameter]
        intervention[parameter] = intervention_config[campaign_parameter]

    return intervention


def get_parameter_map(form_class):
    parameter_map = {}

    for attribute_name in vars(form_class)['base_fields']:
        if attribute_name != "start_day" and attribute_name != "number_of_repetitions" and \
           attribute_name != "timesteps_between_repetitions" and attribute_name != "max_number_of_distributions" and \
           attribute_name != "demographic_coverage" and attribute_name != "DELETE" and attribute_name != 'name':
                parameter_map[attribute_name] = convert_underscore_lower_to_underscore_upper(attribute_name)

    return parameter_map


def get_name_for_url(name):
    if name in intervention_name_to_name_for_url_map:
        return intervention_name_to_name_for_url_map[name]
    else:
        raise ValueError('Intervention name of ' + str(name) + ' does not have a valid url.')


def add_entry_to_intervention(intervention, field_name, value):
    event_coordinator_config = intervention['Event_Coordinator_Config']
    intervention_config = event_coordinator_config['Intervention_Config']

    if field_name == 'start_day':
        intervention['Start_Day'] = int(value)
    elif field_name == 'max_number_of_distributions':
        event_coordinator_config['Number_Distributions'] = int(value)
    elif field_name == 'demographic_coverage':
        event_coordinator_config['Demographic_Coverage'] = float(value)
    elif field_name == 'number_of_repetitions':
        event_coordinator_config['Number_Repetitions'] = int(value)
    elif field_name == 'timesteps_between_repetitions':
        event_coordinator_config['Timesteps_Between_Repetitions'] = int(value)
    else:
        campaign_field_name = convert_underscore_lower_to_underscore_upper(field_name)

        intervention_config[campaign_field_name] = convert_to_number(value)


def convert_underscore_lower_to_underscore_upper(original_string):
    split_original_string = original_string.split('_')

    new_string = ''

    for i in range(len(split_original_string)):
        new_string += split_original_string[i].capitalize()

        if i < len(split_original_string) - 1:
            new_string += '_'

    return new_string


def convert_camel_case_to_human_readable(camel_cased_string):
    return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', camel_cased_string)


def convert_to_number(string):
    # Tries to convert to an int, if it fails it tries float, if it fails it returns it as is because it is not
    # convertible.
    try:
        return int(string)
    except ValueError:
        try:
            return float(string)
        except ValueError:
            return string