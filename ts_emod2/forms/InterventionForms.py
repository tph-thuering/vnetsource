from django import forms


DURABILITY_TIME_PROFILES = [('BOXDURABILITY', 'Box Durability'),
                            ('DECAYDURABILITY', 'Decay Durability'),
                            ('BOXDECAYDURABILITY', 'Box Decay Durability')]

BEDNET_TYPES = [('Barrier', 'Barrier'),
                ('ITN', 'ITN'),
                ('LLIN', 'LLIN'),
                ('Retreatment', 'Retreatment')]

ANTIBODY_TYPE = [('CSP', 'CSP'),
                 ('MSP1', 'MSP1'),
                 ('PfEMP1_minor', 'PfEMP1 Minor'),
                 ('PfEMP1_major', 'PfEMP1 Major')]

LARVICIDE_TARGETS = [('Larvicides_TemporaryRainfall', 'Temporary Rainfall'),
                     ('Larvicides_WaterVegetation', 'Water Vegetation'),
                     ('Larvicides_HumanPopulation', 'Human Population'),
                     ('Larvicides_Constant', 'Constant'),
                     ('Larvicides_AllHabitats', 'All Habitats')]

OUTBREAK_SOURCES = [('PrevalenceIncrease', 'Prevalence Increase'),
                    ('ImportCases', 'Import Cases')]

DOSING_TYPES = [('SingleDose', 'Single Dose'),
                ('FullTreatmentCourse', 'Full Treatment Course'),
                ('Prophylaxis', 'Prophylaxis'),
                ('SingleDoseWhenSymptom', 'Single Dose On Symptom'),
                ('FullTreatmentWhenSymptom', 'Full Treatment On Symptom'),
                ('SingleDoseParasiteDetect', 'Single Dose On Parasite Detection'),
                ('FullTreatmentParasiteDetect', 'Full Treatment On Parasite Detection'),
                ('SingleDoseNewDetectionTech', 'Single Dose On New Detection Tech'),
                ('FullTreatmentNewDetectionTech', 'Full Treatment On New Detection Tech')]

DRUG_TYPES = [('Artemether_Lumefantrine', 'Artemether Lumefantrine'),
              ('Artemisinin', 'Artemisinin'),
              ('Chloroquine', 'Chloroquine'),
              ('GenPreerythrocytic', 'Gen Pre-Erythrocytic'),
              ('GenTransBlocking', 'Gen Trans Blocking'),
              ('Primaquine', 'Primaquine'),
              ('Quinine', 'Quinine'),
              ('SP', 'SP'),
              ('Tafenoquine', 'Tafenoquine')]

VACCINE_TYPES = [('AcquisitionBlocking', 'Acquisition Blocking'),
                 ('Generic', 'Generic'),
                 ('MortalityBlocking', 'Mortality Blocking'),
                 ('TransmissionBlocking', 'Transmission Blocking')]


class BaseInterventionForm(forms.Form):
    start_day = forms.IntegerField(initial=0)
    number_of_repetitions = forms.IntegerField(initial=0)
    timesteps_between_repetitions = forms.IntegerField(initial=0)
    max_number_of_distributions = forms.IntegerField(initial=0)
    demographic_coverage = forms.FloatField(initial=100.0)


class AntimalarialDrugForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Antimalarial Drug")
    cost_to_consumer = forms.FloatField(initial=10.0)
    dosing_type = forms.ChoiceField(choices=DOSING_TYPES, initial=DOSING_TYPES[0][0])
    drug_type = forms.ChoiceField(choices=DRUG_TYPES, initial=DRUG_TYPES[0][0])


class HumanHostSeekingTrapForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Human Host Seeking Trap")
    attract_rate = forms.FloatField(initial=0.5)
    cost_to_consumer = forms.FloatField(initial=3.75)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    killing_rate = forms.FloatField(initial=0.5)
    primary_decay_time_constant = forms.FloatField(initial=3650.0)
    secondary_decay_time_constant = forms.FloatField(initial=3650.0)


class InsectKillingFenceForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Insect Killing Fence")
    cost_to_consumer = forms.FloatField(initial=10.0)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    killing = forms.FloatField(initial=1.0)
    primary_decay_time_constant = forms.FloatField(initial=1.0)
    secondary_decay_time_constant = forms.FloatField(initial=1.0)


class IRSHousingModificationForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="IRS Housing Modification")
    blocking_rate = forms.FloatField(initial=1.0)
    cost_to_consumer = forms.FloatField(initial=8.0)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    killing_rate = forms.FloatField(initial=1.0)
    primary_decay_time_constant = forms.FloatField(initial=3650.0)
    secondary_decay_time_constant = forms.FloatField(initial=3650.0)


class LarvicideForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Larvicide")
    cost_to_consumer = forms.FloatField(initial=10.0)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    killing = forms.FloatField(initial=1.0)
    primary_decay_time_constant = forms.FloatField(initial=1.0)
    reduction = forms.FloatField(initial=1.0)
    secondary_decay_time_constant = forms.FloatField(initial=1.0)
    target = forms.ChoiceField(choices=LARVICIDE_TARGETS, initial=LARVICIDE_TARGETS[0][0])


class OutbreakForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Outbreak")
    antigen = forms.FloatField(initial=0.0)
    genome = forms.FloatField(initial=0.0)
    import_age = forms.IntegerField(initial=365)
    outbreak_source = forms.ChoiceField(choices=OUTBREAK_SOURCES, initial=OUTBREAK_SOURCES[0][0])


class OvipositionTrapForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Oviposition Trap")
    cost_to_consumer = forms.FloatField(initial=10.0)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    killing = forms.FloatField(initial=1.0)
    primary_decay_time_constant = forms.FloatField(initial=1.0)
    secondary_decay_time_constant = forms.FloatField(initial=1.0)
    target = forms.ChoiceField(choices=LARVICIDE_TARGETS, initial=LARVICIDE_TARGETS[0][0])  # Don't know why this uses larvicide targets too


class RTSSVaccineForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="RTSS Vaccine")
    antibody_type = forms.ChoiceField(choices=ANTIBODY_TYPE, initial=ANTIBODY_TYPE[0][0])
    antibody_variant = forms.FloatField(initial=0.0)
    boosted_antibody_concentration = forms.FloatField(initial=1.0)
    cost_to_consumer = forms.FloatField(initial=3.75)


class SimpleBednetForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Simple Bednet")
    bednet_type = forms.ChoiceField(choices=BEDNET_TYPES, initial=BEDNET_TYPES[0][0])
    blocking_rate = forms.FloatField(initial=0.5)
    cost_to_consumer = forms.FloatField(initial=3.75)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    killing_rate = forms.FloatField(initial=0.5)
    primary_decay_time_constant = forms.FloatField(initial=3650.0)
    secondary_decay_time_constant = forms.FloatField(initial=3650.0)


class SimpleVaccineForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Simple Vaccine")
    cost_to_consumer = forms.FloatField(initial=10.0)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    primary_decay_time_constant = forms.FloatField(initial=1.0)
    reduced_acquire = forms.FloatField(initial=1.0)
    reduced_mortality = forms.FloatField(initial=1.0)
    reduced_transmit = forms.FloatField(initial=1.0)
    secondary_decay_time_constant = forms.FloatField(initial=1.0)
    vaccine_take = forms.FloatField(initial=1.0)
    vaccine_type = forms.ChoiceField(choices=VACCINE_TYPES, initial=VACCINE_TYPES[0][0])


class SpatialRepellentForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Spatial Repellent")
    cost_to_consumer = forms.FloatField(initial=10.0)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    primary_decay_time_constant = forms.FloatField(initial=1.0)
    reduction = forms.FloatField(initial=1.0)
    secondary_decay_time_constant = forms.FloatField(initial=1.0)


class SpatialRepellentHousingModificationForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Spatial Repellent Housing Modification")
    blocking_rate = forms.FloatField(initial=1.0)
    cost_to_consumer = forms.FloatField(initial=8.0)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    killing_rate = forms.FloatField(initial=1.0)
    primary_decay_time_constant = forms.FloatField(initial=3650.0)
    secondary_decay_time_constant = forms.FloatField(initial=3650.0)


class SugarTrapForm(BaseInterventionForm):
    name = forms.CharField(widget=forms.HiddenInput(), initial="Sugar Trap")
    cost_to_consumer = forms.FloatField(initial=10.0)
    durability_time_profile = forms.ChoiceField(choices=DURABILITY_TIME_PROFILES, initial=DURABILITY_TIME_PROFILES[0][0])
    killing_rate = forms.FloatField(initial=1.0)
    primary_decay_time_constant = forms.FloatField(initial=1.0)
    reduction = forms.FloatField(initial=1.0)
    secondary_decay_time_constant = forms.FloatField(initial=1.0)