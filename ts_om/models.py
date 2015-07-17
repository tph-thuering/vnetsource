from StringIO import StringIO
import datetime
from xml.etree.ElementTree import ParseError

from django.core.exceptions import MultipleObjectsReturned
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from lxml import etree
from lxml.etree import XMLSyntaxError
import vecnet.openmalaria.scenario

from data_services.models import Simulation, SimulationGroup, DimUser


class ExperimentFile(models.Model):
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='ts_om/experiments/%Y/%m/%d')
    user = models.ForeignKey(User)
    test_sim_group = models.ForeignKey(SimulationGroup, null=True, related_name="test_submit_group")
    sim_group = models.ForeignKey(SimulationGroup, null=True, related_name="submit_group")

    def __unicode__(self):
        return self.name

    @property
    def state(self):
        pass


class BaselineScenario(models.Model):
    name = models.CharField(max_length=200)
    xml = models.TextField()

    def __unicode__(self):
        return self.name


class DemographicsSnippet(models.Model):
    name = models.CharField(max_length=200)
    maximum_age_yrs = models.CharField(max_length=200)
    xml = models.TextField()
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=200)

    def __unicode__(self):
        return self.title


class ModelSnippet(models.Model):
    """
    These snippets provide parameters calibrated by model fitting as well as some
model options chosen to differentiate the model. Downloaded from
https://code.google.com/p/openmalaria/source/browse/v32/models+5-day/?repo=snippets

See the publication "Ensemble Modeling of the Likely Public Health Impact of a
Pre-Erythrocytic Malaria Vaccine", Smith et al, for a description of these
models:
http://www.plosmedicine.org/article/info%3Adoi%2F10.1371%2Fjournal.pmed.1001157

Summary of the description is available on
http://www.plosmedicine.org/article/fetchObject.action?uri=info:doi/10.1371/journal.pmed.1001157.t002&representation=PNG_L
    """
    name = models.CharField(max_length=200)
    xml = models.TextField()

    def __unicode__(self):
        return self.name


class Scenario(models.Model):
    xml = models.TextField()
    start_date = models.IntegerField(default=datetime.datetime.now().year)
    user = models.ForeignKey(User)
    simulation = models.ForeignKey(Simulation, null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    is_public = models.BooleanField(default=False)

    # -------------------------------------------------
    # name property setter and getter
    @property
    def name(self):
        try:
            tree = etree.parse(StringIO(str(self.xml)))
        except XMLSyntaxError:
            name = "Invalid xml document"
        else:
            try:
                name = tree.getroot().xpath('@name')[0]
            except IndexError:
                name = "Unnamed scenario"
        return name

    @name.setter
    def name(self, value):
        tree = etree.parse(StringIO(str(self.xml)))
        scenario = tree.getroot()
        scenario.attrib['name'] = value
        self.xml = etree.tostring(tree.getroot(), pretty_print=True)

    #
    # ----------------------------------------------------

    @property
    def status(self):
        try:
            status = self.simulation.status
        except Exception:
            status = None
        return status


class AnophelesSnippet(models.Model):
    # Vector description in /om:scenario/entomology/vector/anopheles section of xml
    anopheles = models.TextField(null=False, blank=False)
    # anophelesParams in /om:scenario/interventions/human/component/GVI section.
    # Only required if GVI interventions are applied.
    gvi_anophelesParams = models.TextField(null=True, blank=True)
    # anophelesParams in /om:scenario/interventions/human/component/ITN section.
    # Only required if ITN interventions are applied.
    itn_anophelesParams = models.TextField(null=True, blank=True)
    # anophelesParams in /om:scenario/interventions/human/component/IRS section.
    # Only required if IRS interventions are applied.
    irs_anophelesParams = models.TextField(null=True, blank=True)

    @property
    def name(self):
        try:
            tree = etree.parse(StringIO(str(self.anopheles)))
        except XMLSyntaxError:
            name = "Invalid xml snippet"
        else:
            try:
                name = tree.getroot().xpath('@mosquito')[0]
            except IndexError:
                name = "Unnamed anopheles snippet"
        return name

    def __unicode__(self):
        return self.name


class InterventionComponent(models.Model):
    name = models.CharField(max_length=200)
    tag = models.CharField(max_length=200)

    def __unicode__(self):
        return self.name


class InterventionSnippet(models.Model):
    name = models.CharField(max_length=200)
    component = models.ForeignKey(InterventionComponent, null=False)
    xml = models.TextField(null=False, blank=False)

    def __unicode__(self):
        return self.name


class Experiment(models.Model):
    """
    OpenMalaria Experiment is just a collection of Scenarios.
    We also need SimulationGroup - to track status of this Experiment,
    and optional base - to show differences between individual scenarios and base scenario of this Experiment
    """
    name = models.TextField()
    description = models.TextField(blank=True, default="")
    sim_group = models.ForeignKey(SimulationGroup, null=True, blank=True)
    # base = models.TextField(null=True, blank=True)
    #
    # Experiment Specification is JSON document that includes experiment template, Sweep Memorandum
    # and describes which combinations of sweeps and arms will be generated.
    # More details: https://docs.google.com/document/d/1SSBqc-0fDhsGtMuBWsGfM2m2GxTAT8Io7oikoEF4sRQ/edit
    #
    # If Experiment was generated expernally, Experiment Specification may not be available
    experiment_specification = models.TextField(null=True, blank=True)

    def get_sweeps(self):
        """ Return list of all sweeps in this experiment
        This function implies that this is full factorial experiment
        :return dictionary - sweep name:list of arm names for that sweep
        """
        # Get list of sweep that belongs to this Experiment
        sweeps_names = SweepArmMappingToScenario.objects.filter(experiment=self).distinct(["sweep_name"])
        sweeps = dict()
        for sweep_name in sweeps_names:
            # Create list of arm names
            arms = [arm.name for arm in
                    SweepArmMappingToScenario.objects.filter(experiment=self, sweep_name=sweep_name)]
            sweeps[sweep_name] = arms
        return sweeps

    def get_scenario(self, keys):
        sweep = SweepArmMappingToScenario.objects.filter(experiment=self, **keys)
        if sweep.count() == 1:
            return sweep[0].scenario
        if sweep.count() == 0:
            return None
        raise MultipleObjectsReturned("Too many scenarios found, key list maybe incomplete")


class SweepArmMappingToScenario(models.Model):
    """
    Each Scenario in Experiment will be associated with a list values for each sweep (one value for one parameter)
    """
    experiment = models.ForeignKey(Experiment)
    scenario = models.ForeignKey(Scenario)
    sweep_name = models.CharField(max_length=127)
    arm_name = models.CharField(max_length=127)


# class ScenarioTemplate(models.Model):
# pass


class RunMetaData():
    # results_base_url = 'https://ci.vecnet.org/ts_emod/output/results_viewer/'

    def __init__(self, scenario):
        self.scenario = scenario
        self.getMetaData()

    def getMetaData(self):
        # Stuff retrieved from derived
        scenario = self.scenario
        simulation = scenario.simulation
        django_user = scenario.user
        user = DimUser.objects.get_or_create(username=django_user.username)

        try:
            scenario_wrapper = vecnet.openmalaria.scenario.Scenario(scenario.xml)
        except ParseError:
            scenario_wrapper = None

        try:
            duration_in_years = scenario_wrapper.monitoring.surveys[-1] * 5 / 365
        except AttributeError:
            duration_in_years = 0

        meta_data = scenario.metadata

        self.coordinates = []
        self.species = []

        self.creator = user.username  # user.first_name + user.last_name
        self.results_url = ""
        # self.results_url = "https://ci-qa.vecnet.org" + reverse("ts_emod_run_details", args=[dimRun.id, experiment.id])
        # self.coordinates = self.getCoordinates()
        self.coordinates = ["", ""]
        self.time_period = [scenario.start_date, scenario.start_date + duration_in_years]
        # for specie in configJson['parameters']['Vector_Species_Params']:
        # self.species.append("An. " + specie)
        self.species.append("")

        # for intervention in campaignJson['Events']:
        #     interventions.append(self.Intervention(intervention))
        # self.interventions = list(set([intervention.name for intervention in interventions]))
        self.interventions = [""]
        self.interventions_set = list(set(self.interventions))
        self.model_version = simulation.version
        self.simulation_type = ""  # configJson['parameters']['Simulation_Type']
        self.run_date = scenario.time_launched

        # Stuff retrieved from database
        if meta_data is None:
            meta_data = {}

        self.is_public = meta_data.get('isPublic', 'True')
        self.title = self.scenario.name  # metaData.get('title', '')
        self.citation = meta_data.get('citation', '')
        self.location = meta_data.get('location', '')
        self.tags = meta_data.get('tags', '')
        self.description = meta_data.get('description', '')
        self.parameters_of_interest = meta_data.get('parametersOfInterest', '')
        self.metadata_last_update_date = meta_data.get('metaDataLastUpdateDate', self.run_date)

        # Generate autoname/autoid
        # interventions_label = ""
        # unique_labels = set()
        # for intervention in interventions:
        #     unique_labels.add(intervention.type)
        # for label in unique_labels:
        #     interventions_label += label
        #
        # days = (scenario.end_date_key.timestamp - scenario.start_date_key.timestamp).days
        # if days < 365:
        #     duration = "%sm" % (days / 30)
        # else:
        #     duration = "%sy" % (days / 365)
        # self.autoname = str(self.creator) + str(interventions_label) + \
        #                 str(self.location.replace(" ", "").replace(",", "")) + str(duration) + str(self.scenario.id)
        self.autoname = "AUTO"

    def getCoordinates(self):
        # location = GisBaseTable.objects.all().filter(id=self.scenario.location_key.geom_key)
        # Ignore PyCharm warning below
        # GisBaseTable.objects is models.GeoManager() and it does produce GeoQuerySet which has centroid function
        # Somehow PyCharm thinks it is normal QuerySet
        # Please refer to https://docs.djangoproject.com/en/dev/ref/contrib/gis/geoquerysets/#centroid for more details
        # centroid = location.centroid(model_att='centroid')[0].centroid
        # return {'latitude': centroid.y, 'longitude': centroid.x}
        pass

    def saveMetaData(self):
        if self.scenario.metadata is None:
            self.scenario.metadata = {}

        self.scenario.metadata['isPublic'] = self.is_public
        # self.dimRun.metadata['title'] = self.title
        self.scenario.name = self.title
        self.scenario.metadata['citation'] = self.citation
        self.scenario.metadata['location'] = self.location
        self.scenario.metadata['tags'] = self.tags
        self.scenario.metadata['description'] = self.description
        self.scenario.metadata['parametersOfInterest'] = self.parameters_of_interest
        self.scenario.metadata['metaDataLastUpdateDate'] = timezone.now()
        self.scenario.save()
