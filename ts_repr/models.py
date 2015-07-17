from django.db import models

from data_services.models import SimulationInputFile, DimUser, DimBaseline
from ts_emod.fields import JSONConfigField                                               # Will go away

import json
from jsonfield import JSONField


class ModelVersion(models.Model):
    model = models.TextField()
    version_major = models.IntegerField(default=0)
    version_minor = models.IntegerField(default=0)
    version_build = models.IntegerField(default=0)
    version_revision = models.IntegerField(default=0)

    def __str__(self):
        return self.model + str(self.version_major) + "." + str(self.version_minor) + "." + str(self.version_build) \
            + "." + str(self.version_revision)

    class Meta:
        db_table = 'ts_repr_model_version'
        # Changing model name in Django admin panel to ModelVersion
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "ModelVersion"
        verbose_name_plural = "ModelVersions"


class EMODSnippet(models.Model):
    name = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    snippet = JSONConfigField()  # Holds json snippet

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_repr_emod_snippet'
        # Changing model name in Django admin panel to EMODSnippet
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "EMODSnippet"
        verbose_name_plural = "EMODSnippets"


class OMSnippet(models.Model):
    name = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    snippet = models.TextField()  # Holds XML snippet

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_repr_om_snippet'
        # Changing model name in Django admin panel to EmodSnippet
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "OMSnippet"
        verbose_name_plural = "OMSnippets"


class RepresentativeScenario(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    user = models.ForeignKey(DimUser, db_column='user_key', null=False)

    steps_complete = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    time_created = models.DateTimeField(null=False)
    time_deleted = models.DateTimeField(null=True)

    emod_scenario = models.ForeignKey(DimBaseline)
    # om_scenario = models.ForeignKey

    choices = JSONConfigField(null=True, blank=True)  # Holds choices for each step in json form
    valid_model_versions = models.ManyToManyField(ModelVersion,
                                                  db_table="ts_repr_representative_scenario__valid_model_versions")

    def __str__(self):
        return self.name

    @property
    def derived_name(self):
        current_json = json.loads(self.choices)

        name = ""
        if 'weather_id' in current_json:
            name += self.get_weather_name(current_json['weather_id']) + "-"

            if 'demographics_id' in current_json:
                name += self.get_demographics_name(current_json['demographics_id']) + "-"

                if 'species_page' in current_json:
                    for species in current_json['species_page']['species']:
                        name += self.get_species_name(species['species_id']) + "-"

                    name = name[:-1]  # Remove the extra -

        return name

    def get_weather_name(self, weather_id):
        weather = RepresentativeWeather.objects.get(id=weather_id)
        return weather.name

    def get_demographics_name(self, demographics_id):
        demographics = RepresentativeDemographics.objects.get(id=demographics_id)
        return demographics.name

    def get_species_name(self, species_id):
        species = RepresentativeSpecies.objects.get(id=species_id)
        return species.name

    class Meta:
        db_table = 'ts_repr_representative_scenario'
        # Changing model name in Django admin panel to RepresentativeScenario
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "RepresentativeScenario"
        verbose_name_plural = "RepresentativeScenarios"


class RepresentativeWeather(models.Model):
    name = models.TextField()
    precalibration_name = models.TextField()
    short_description = models.TextField()
    description = models.TextField(null=True, blank=True)

    emod_weather = models.ManyToManyField(SimulationInputFile, null=True, blank=True)
    om_seasonality = models.ForeignKey(OMSnippet, null=True, blank=True)  # Holds XML snippet

    emod_weather_rainfall_file_location = models.TextField(null=True, blank=True)
    emod_weather_humidity_file_location = models.TextField(null=True, blank=True)
    emod_weather_temperature_file_location = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=False)
    valid_model_versions = models.ManyToManyField(ModelVersion,
                                                  db_table="ts_repr_representative_weather__valid_model_versions")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_repr_representative_weather'
        # Changing model name in Django admin panel to RepresentativeWeather
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "RepresentativeWeather"
        verbose_name_plural = "RepresentativeWeather"


class RepresentativeDemographics(models.Model):
    name = models.TextField()
    precalibration_name = models.TextField()
    description = models.TextField(null=True, blank=True)
    type = models.TextField(null=False)

    emod_demographics = models.ForeignKey(SimulationInputFile, related_name="uncompiled", null=True, blank=True)
    emod_demographics_compiled = models.ForeignKey(SimulationInputFile, related_name="compiled", null=True, blank=True)
    om_demographics = models.ForeignKey(OMSnippet, null=True, blank=True)  # Holds XML snippet

    emod_demographics_compiled_file_location = models.TextField(null=True, blank=True)

    is_active = models.BooleanField(default=False)
    valid_model_versions = models.ManyToManyField(ModelVersion,
                                                  db_table="ts_repr_representative_demographics__valid_model_versions")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_repr_representative_demographics'
        # Changing model name in Django admin panel to RepresentativeDemographics
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "RepresentativeDemographics"
        verbose_name_plural = "RepresentativeDemographics"


class RepresentativeSpeciesParameter(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)

    emod_high = models.FloatField()
    emod_medium = models.FloatField()
    emod_low = models.FloatField()

    om_high = models.FloatField()
    om_medium = models.FloatField()
    om_low = models.FloatField()

    is_active = models.BooleanField(default=False)
    valid_model_versions = models.ManyToManyField(ModelVersion,
                                                  db_table="ts_repr_representative_species_parameter__valid_model_versions")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_repr_representative_species_parameter'
        # Changing model name in Django admin panel to RepresentativeSpeciesParameter
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "RepresentativeSpeciesParameter"
        verbose_name_plural = "RepresentativeSpeciesParameters"


class RepresentativeSpeciesParameterDefault(models.Model):
    parameter = models.ForeignKey(RepresentativeSpeciesParameter)
    default = models.TextField()

    def __str__(self):
        return "Parameter: " + str(self.parameter.id) + ", Default: " + self.default

    class Meta:
        db_table = 'ts_repr_representative_species_parameter_default'
        # Changing model name in Django admin panel to RepresentativeSpeciesParameterDefault
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "RepresentativeSpeciesParameterDefault"
        verbose_name_plural = "RepresentativeSpeciesParameterDefaults"


class RepresentativeSpeciesHabitatType(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    value = models.TextField()

    is_active = models.BooleanField(default=False)
    # tb_table changed from "ts_repr_representative_species_habitat_type__valid_model_versions" to
    # ts_repr_representative_species_habitat_type__valid_model_version because max default length of PostgreSQL
    # identificator is 63 bytes, so table name in database is truncated to
    # "ts_repr_representative_species_habitat_type__valid_model_versio"
    valid_model_versions = models.ManyToManyField(ModelVersion,
                                                  db_table="ts_repr_representative_species_habitat_type__valid_model_versio")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_repr_representative_species_habitat_type'
        # Changing model name in Django admin panel to RepresentativeSpeciesHabitatType
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "RepresentativeSpeciesHabitatType"
        verbose_name_plural = "RepresentativeSpeciesHabitatTypes"


class RepresentativeSpecies(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)

    # These hold all values for a species. However a few parameters (ie the ones editable on the
    # species representative page) will be overwritten by the parameters held in the variable
    # called parameters, below these snippets
    emod_snippet = models.ForeignKey(EMODSnippet, null=True, blank=True)  # Holds Json snippet
    om_snippet = models.ForeignKey(OMSnippet, null=True, blank=True)  # Holds XML snippet

    parameters = models.ManyToManyField(RepresentativeSpeciesParameter,
                                        db_table="ts_repr_representative_species__parameters")
    parameter_defaults = models.ManyToManyField(RepresentativeSpeciesParameterDefault,
                                                db_table="ts_repr_representative_species__parameter_defaults")
    habitat_type = models.ForeignKey(RepresentativeSpeciesHabitatType)

    is_active = models.BooleanField(default=False)
    valid_model_versions = models.ManyToManyField(ModelVersion,
                                                  db_table="ts_repr_representative_species__valid_model_versions")

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_repr_representative_species'
        # Changing model name in Django admin panel to RepresentativeSpecies
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "RepresentativeSpecies"
        verbose_name_plural = "RepresentativeSpecies"


class RepresentativePrecomputedEIR(models.Model):
    input_files = models.ManyToManyField(SimulationInputFile)
    target_EIR = models.FloatField()

    weather = models.ForeignKey(RepresentativeWeather)
    demographics = models.ForeignKey(RepresentativeDemographics)

    species1 = models.ForeignKey(RepresentativeSpecies, related_name="species1", null=True, blank=True)
    species2 = models.ForeignKey(RepresentativeSpecies, related_name="species2", null=True, blank=True)
    species3 = models.ForeignKey(RepresentativeSpecies, related_name="species3", null=True, blank=True)
    species4 = models.ForeignKey(RepresentativeSpecies, related_name="species4", null=True, blank=True)

    species1_parameters = models.ManyToManyField(RepresentativeSpeciesParameter, related_name="species1_parameters",
                                                 null=True, blank=True)
    species2_parameters = models.ManyToManyField(RepresentativeSpeciesParameter, related_name="species2_parameters",
                                                 null=True, blank=True)
    species3_parameters = models.ManyToManyField(RepresentativeSpeciesParameter, related_name="species3_parameters",
                                                 null=True, blank=True)
    species4_parameters = models.ManyToManyField(RepresentativeSpeciesParameter, related_name="species4_parameters",
                                                 null=True, blank=True)

    def __str__(self):
        string = "Precomputed x_temp_larval_habitat of " + str(self.xtlh) + " for target EIR of " \
            + str(self.target_EIR) + " with the following parameters: " + str(self.weather) + ", " \
            + str(self.demographics) + ", "

        if self.species1 is not None:
            string += str(self.species1) + " with id " + str(self.species1.id) + " and parameters ("
            the_parameters = self.species1_parameters.all().defer('content')
            for parameter in the_parameters:
                string += parameter + ", "
            string += "), "

        if self.species2 is not None:
            string += str(self.species2) + " with id " + str(self.species2.id) + " and parameters ("
            the_parameters = self.species2_parameters.all().defer('content')
            for parameter in the_parameters:
                string += parameter + ", "
            string += "), "

        if self.species3 is not None:
            string += str(self.species3) + " with id " + str(self.species3.id) + " and parameters ("
            the_parameters = self.species3_parameters.all().defer('content')
            for parameter in the_parameters:
                string += parameter + ", "
            string += "), "

        if self.species4 is not None:
            string += str(self.species4) + " with id " + str(self.species4.id) + " and parameters ("
            the_parameters = self.species4_parameters.all().defer('content')
            for parameter in the_parameters:
                string += parameter + ", "
            string += ")"

        return string

    class Meta:
        db_table = 'ts_repr_representative_precomputed_EIR'
        # Changing model name in Django admin panel to RepresentativePrecomputedEIR
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "RepresentativePrecomputedEIR"
        verbose_name_plural = "RepresentativePrecomputedEIRs"

























































# class EMODSnippet(models.Model):
#     name = models.TextField(null=True, blank=True)
#     description = models.TextField(null=True, blank=True)
#     snippet = JSONField()  # Holds json snippet
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         db_table = 'ts_repr_emod_snippet'
#         # Changing model name in Django admin panel to EMODSnippet
#         # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
#         # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
#         verbose_name = "EMODSnippet"
#         verbose_name_plural = "EMODSnippets"
#
#
# class OMSnippet(models.Model):
#     name = models.TextField(null=True, blank=True)
#     description = models.TextField(null=True, blank=True)
#     snippet = models.TextField()  # Holds XML snippet
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         db_table = 'ts_repr_om_snippet'
#         # Changing model name in Django admin panel to EmodSnippet
#         # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
#         # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
#         verbose_name = "OMSnippet"
#         verbose_name_plural = "OMSnippets"
#
#
# class Weather(models.Model):
#     name = models.TextField()
#     description = models.TextField(null=True, blank=True)
#
#     emod_weather = models.ManyToManyField(SimulationInputFile, null=True, blank=True)
#     om_seasonality = models.ForeignKey(OMSnippet, null=True, blank=True)  # Holds XML snippet
#
#     emod_weather_rainfall_file_location = models.TextField(null=True, blank=True)
#     emod_weather_humidity_file_location = models.TextField(null=True, blank=True)
#     emod_weather_temperature_file_location = models.TextField(null=True, blank=True)
#
#     is_active = models.BooleanField(default=False)
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         db_table = 'ts_repr_weather'
#         # Changing model name in Django admin panel to Weather
#         # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
#         # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
#         verbose_name = "Weather"
#         verbose_name_plural = "Weather"
#
#
# class Demographics(models.Model):
#     name = models.TextField()
#     description = models.TextField(null=True, blank=True)
#     type = models.TextField(null=False)
#
#     emod_demographics = models.ForeignKey(SimulationInputFile, related_name="uncompiled", null=True, blank=True)
#     emod_demographics_compiled = models.ForeignKey(SimulationInputFile, related_name="compiled", null=True, blank=True)
#     om_demographics = models.ForeignKey(OMSnippet, null=True, blank=True)  # Holds XML snippet
#
#     emod_demographics_compiled_file_location = models.TextField(null=True, blank=True)
#
#     is_active = models.BooleanField(default=False)
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         db_table = 'ts_repr_demographics'
#         # Changing model name in Django admin panel to Demographics
#         # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
#         # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
#         verbose_name = "Demographics"
#         verbose_name_plural = "Demographics"
#
#
# class Species(models.Model):
#     name = models.TextField()
#     description = models.TextField(null=True, blank=True)
#
#     # These hold all values for a species. However a few parameters (ie the ones editable on the
#     # species representative page) will be overwritten by the parameters held in the variable
#     # called parameters, below these snippets
#     emod_snippet = models.ForeignKey(EMODSnippet, null=True, blank=True)  # Holds Json snippet
#     om_snippet = models.ForeignKey(OMSnippet, null=True, blank=True)  # Holds XML snippet
#
#     #parameters = JSONField()
#
#     is_active = models.BooleanField(default=False)
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         db_table = 'ts_repr_species'
#         # Changing model name in Django admin panel to Species
#         # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
#         # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
#         verbose_name = "Species"
#         verbose_name_plural = "Species"