from django.db import models

from vecnet.emod.demographics import compile_demographics

from data_services.models import DimUser, Folder, Simulation

from jsonfield import JSONField

# class Meta:
#     db_table = 'ts_emod2_location'
#     verbose_name = "Location"
#     verbose_name_plural = "Locations"
# Changing model name in Django admin panel
# http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
# https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name


class Location(models.Model):
    name = models.TextField()
    # This will be null for public and defined for private
    user = models.ForeignKey(DimUser, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    deletion_timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_emod2_location'
        verbose_name = "Location"
        verbose_name_plural = "Locations"


class ExperimentSpecification(models.Model):
    # This will be null unless the user wants to save a copy of this specific specification for later use
    user = models.ForeignKey(DimUser, null=True, blank=True)
    specification = JSONField()

    def __str__(self):
        return self.specification

    class Meta:
        db_table = 'ts_emod2_experiment_specification'
        verbose_name = "ExperimentSpecification"
        verbose_name_plural = "ExperimentSpecifications"


class Experiment(models.Model):
    experiment_specification = models.ForeignKey(ExperimentSpecification)

    def __str__(self):
        return self.experiment_specification

    class Meta:
        db_table = 'ts_emod2_experiment'
        verbose_name = "Experiment"
        verbose_name_plural = "Experiments"


class ScenarioTemplate(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    user = models.ForeignKey(DimUser, null=True, blank=True)
    location = models.ForeignKey(Location)
    simulation = models.ForeignKey(Simulation)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_emod2_scenario_template'
        verbose_name = "ScenarioTemplate"
        verbose_name_plural = "ScenarioTemplates"


class Scenario(models.Model):
    name = models.TextField()
    description = models.TextField(null=True, blank=True)
    user = models.ForeignKey(DimUser)

    simulation = models.ForeignKey(Simulation, related_name='emod_scenario_set')
    location = models.ForeignKey(Location, null=True, blank=True)
    template = models.ForeignKey(ScenarioTemplate, null=True, blank=True)
    folder = models.ForeignKey(Folder, null=True, blank=True)
    experiment_specification = models.ForeignKey(ExperimentSpecification, null=True, blank=True)
    experiment = models.ForeignKey(Experiment, null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)

    creation_timestamp = models.DateTimeField(auto_now=True)
    last_modified = models.DateTimeField(auto_now=True)
    deletion_timestamp = models.DateTimeField(null=True, blank=True)

    is_public = models.BooleanField(default=False)

    metadata = JSONField()  # For the metadata page
    extra_metadata = JSONField()  # For other things like representative scenario information and for calibration status

    CONFIG_FILENAME = 'config.json'
    CAMPAIGN_FILENAME = 'campaign.json'
    UNCOMPILED_DEMOGRAPHICS_FILENAME = 'demographics.json'
    COMPILED_DEMOGRAPHICS_FILENAME = 'demographics.compiled.json'
    RAINFALL_JSON_FILENAME = 'rainfall.bin.json'
    RAINFALL_BIN_FILENAME = 'rainfall.bin'
    HUMIDITY_JSON_FILENAME = 'humidity.bin.json'
    HUMIDITY_BIN_FILENAME = 'humidity.bin'
    TEMPERATURE_JSON_FILENAME = 'temperature.bin.json'
    TEMPERATURE_BIN_FILENAME = 'temperature.bin'
    BINNED_REPORT_FILENAME = 'BinnedReport.json'
    DEMOGRAPHICS_SUMMARY_FILENAME = 'DemographicsSummary.json'
    INSET_CHART_FILENAME = 'InsetChart.json'
    VECTOR_SPECIES_REPORT_FILENAME = 'VectorSpeciesReport.json'

    def get_file_by_type(self, file_type):
        if file_type == 'config':
            return self.config_file
        elif file_type == 'campaign':
            return self.campaign_file
        elif file_type == 'demographics':
            return self.uncompiled_demographics_file
        elif file_type == 'demographics-compiled':
            return self.compiled_demographics_file
        elif file_type == 'rainfall-json':
            return self.rainfall_json_file
        elif file_type == 'rainfall-bin':
            return self.rainfall_bin_file
        elif file_type == 'humidity-json':
            return self.humidity_json_file
        elif file_type == 'humidity-bin':
            return self.humidity_bin_file
        elif file_type == 'temperature-json':
            return self.temperature_json_file
        elif file_type == 'temperature-bin':
            return self.temperature_bin_file
        elif file_type == 'binned-report-json':
            return self.binned_report_json_file
        elif file_type == 'demographics-summary-json':
            return self.demographics_summary_json_file
        elif file_type == 'inset-chart-json':
            return self.inset_chart_json_file
        elif file_type == 'vector-species-report-json':
            return self.vector_species_report_json_file
        else:
            raise ValueError("Invalid file_type of " + file_type)

    def set_file_by_type(self, file_type, contents):
        if file_type == 'config':
            self.config_file.set_contents(contents)
        elif file_type == 'campaign':
            self.campaign_file.set_contents(contents)
        elif file_type == 'demographics':
            compiled_demographics = compile_demographics(contents, None, True)
            self.compiled_demographics_file.set_contents(compiled_demographics)
            self.uncompiled_demographics_file.set_contents(contents)
        elif file_type == 'rainfall-json':
            self.rainfall_json_file.set_contents(contents)
        elif file_type == 'rainfall-bin':
            self.rainfall_bin_file.set_contents(contents)
        elif file_type == 'humidity-json':
            self.humidity_json_file.set_contents(contents)
        elif file_type == 'humidity-bin':
            self.humidity_bin_file.set_contents(contents)
        elif file_type == 'temperature-json':
            self.temperature_json_file.set_contents(contents)
        elif file_type == 'temperature-bin':
            self.temperature_bin_file.set_contents(contents)
        else:
            raise ValueError("Invalid file_type of " + file_type)

    def get_filename_by_type(self, file_type):
        if file_type == 'config':
            return self.CONFIG_FILENAME
        elif file_type == 'campaign':
            return self.CAMPAIGN_FILENAME
        elif file_type == 'demographics':
            return self.UNCOMPILED_DEMOGRAPHICS_FILENAME
        elif file_type == 'demographics-compiled':
            return self.COMPILED_DEMOGRAPHICS_FILENAME
        elif file_type == 'rainfall-json':
            return self.RAINFALL_JSON_FILENAME
        elif file_type == 'rainfall-bin':
            return self.RAINFALL_BIN_FILENAME
        elif file_type == 'humidity-json':
            return self.HUMIDITY_JSON_FILENAME
        elif file_type == 'humidity-bin':
            return self.HUMIDITY_BIN_FILENAME
        elif file_type == 'temperature-json':
            return self.TEMPERATURE_JSON_FILENAME
        elif file_type == 'temperature-bin':
            return self.TEMPERATURE_BIN_FILENAME
        elif file_type == 'binned-report-json':
            return self.BINNED_REPORT_FILENAME
        elif file_type == 'demographics-summary-json':
            return self.DEMOGRAPHICS_SUMMARY_FILENAME
        elif file_type == 'inset-chart-json':
            return self.INSET_CHART_FILENAME
        elif file_type == 'vector-species-report-json':
            return self.VECTOR_SPECIES_REPORT_FILENAME
        else:
            raise ValueError("Invalid file_type of " + file_type)

    @property
    def config_file(self):
        return self.simulation.input_files.get(name=self.CONFIG_FILENAME)

    @property
    def campaign_file(self):
        return self.simulation.input_files.get(name=self.CAMPAIGN_FILENAME)

    @property
    def uncompiled_demographics_file(self):
        return self.simulation.input_files.get(name=self.UNCOMPILED_DEMOGRAPHICS_FILENAME)

    @property
    def compiled_demographics_file(self):
        return self.simulation.input_files.get(name=self.COMPILED_DEMOGRAPHICS_FILENAME)

    @property
    def temperature_json_file(self):
        return self.simulation.input_files.get(name=self.TEMPERATURE_JSON_FILENAME)

    @property
    def temperature_bin_file(self):
        return self.simulation.input_files.get(name=self.TEMPERATURE_BIN_FILENAME)

    @property
    def humidity_json_file(self):
        return self.simulation.input_files.get(name=self.HUMIDITY_JSON_FILENAME)

    @property
    def humidity_bin_file(self):
        return self.simulation.input_files.get(name=self.HUMIDITY_BIN_FILENAME)

    @property
    def rainfall_json_file(self):
        return self.simulation.input_files.get(name=self.RAINFALL_JSON_FILENAME)

    @property
    def rainfall_bin_file(self):
        return self.simulation.input_files.get(name=self.RAINFALL_BIN_FILENAME)

    @property
    def binned_report_json_file(self):
        return self.simulation.simulationoutputfile_set.get(name=self.BINNED_REPORT_FILENAME)

    @property
    def demographics_summary_json_file(self):
        return self.simulation.simulationoutputfile_set.get(name=self.DEMOGRAPHICS_SUMMARY_FILENAME)

    @property
    def inset_chart_json_file(self):
        return self.simulation.simulationoutputfile_set.get(name=self.INSET_CHART_FILENAME)

    @property
    def vector_species_report_json_file(self):
        return self.simulation.simulationoutputfile_set.get(name=self.VECTOR_SPECIES_REPORT_FILENAME)

    def copy(self, include_output=False, should_link_experiment=False, should_link_simulation=False, should_link_simulation_files=False):
        if should_link_simulation and not should_link_simulation_files:
            raise Exception("Impossible to link the simulation but not link the simulation files.")

        if should_link_simulation:
            simulation = self.simulation
        else:
            simulation = self.simulation.copy(include_output, should_link_simulation_files)

        # if self.experiment:
        #     if should_link_experiment:
        #         experiment = self.experiment
        #     else:
        #         experiment = Experiment.objects.create(experiment_specification=self.experiment_specification)
        # else:
        experiment_specification = None
        experiment = None

        new_scenario = Scenario.objects.create(
            name=self.name + ' copy',
            description=self.description,
            user=self.user,
            simulation=simulation,
            location=self.location,
            template=self.template,
            folder=self.folder,
            experiment_specification=experiment_specification,
            experiment=experiment,
            start_date=self.start_date,
            metadata=self.metadata,
            extra_metadata=self.extra_metadata
        )

        return new_scenario

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'ts_emod2_scenario'
        verbose_name = "Scenario"
        verbose_name_plural = "Scenarios"