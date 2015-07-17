# Create your views here.
# PEP 0263
# -*- coding: utf-8 -*-
########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Alexander Vyushkov <Alexander.Vyushkov@nd.edu>
#   Nicolas Reed <nreed4@nd.edu>
########################################################################################################################
from xml.etree.ElementTree import ParseError
from django.core.exceptions import PermissionDenied

from django.core.urlresolvers import reverse
from django.views.generic import FormView
from vecnet.openmalaria.scenario import Scenario
from vecnet.openmalaria.monitoring import get_survey_times

from ts_om import submit
from ts_om.forms import ScenarioSummaryForm
from ts_om.models import Scenario as ScenarioModel

__author__ = 'Alexander'


class ScenarioSummaryView(FormView):
    template_name = "ts_om/summary.html"
    form_class = ScenarioSummaryForm
    model_scenario = None
    scenario = None

    def get_success_url(self):
        return reverse('ts_om.list')

    def get_context_data(self, **kwargs):
        context = super(ScenarioSummaryView, self).get_context_data(**kwargs)
        vectors = []

        for v in self.scenario.entomology.vectors:
            vectors.append(v.mosquito)

        if self.scenario:
            context["scenario_id"] = self.model_scenario.id
            context["name"] = self.model_scenario.name
            context["desc"] = self.model_scenario.description if self.model_scenario.description else ""
            context["deleted"] = self.model_scenario.deleted
            context["version"] = self.scenario.schemaVersion

            if self.model_scenario.simulation:
                context['sim_id'] = self.model_scenario.simulation.id

            context["xml"] = self.scenario.xml

            monitor_info = get_survey_times(self.scenario.monitoring, self.model_scenario.start_date)

            context["monitor_type"] = monitor_info["type"]
            context["monitor_yrs"] = monitor_info["yrs"]
            context["monitor_mos"] = monitor_info["mos"]
            context["timesteps"] = monitor_info["timesteps"]

            context["demography"] = self.scenario.demography.name
            context["pop_size"] = self.scenario.demography.popSize

            context["first_line_drug"] = self.scenario.healthSystem.ImmediateOutcomes.firstLine
            context["vectors"] = vectors
            context["annual_eir"] = self.scenario.entomology.scaledAnnualEIR

            interventions = []
            for component in self.scenario.interventions.human:
                interventions.append(component.id)
            for vectorPop in self.scenario.interventions.vectorPop:
                interventions.append(vectorPop.name)

            context["interventions"] = interventions

        return context

    def get_initial(self):
        initial = {'desc': self.model_scenario.description, 'name': str(self.model_scenario.name)}

        return initial

    def get_form(self, form_class):
        if "scenario_id" in self.kwargs:
            scenario_id = self.kwargs["scenario_id"]
            self.model_scenario = ScenarioModel.objects.get(id=scenario_id)

            if self.request.user != self.model_scenario.user:
                raise PermissionDenied

            try:
                self.scenario = Scenario(self.model_scenario.xml)
            except ParseError:
                self.scenario = None

        return super(ScenarioSummaryView, self).get_form(form_class)

    def form_valid(self, form):
        xml = form.cleaned_data['xml']
        submit_type = form.cleaned_data['submit_type']
        name = form.cleaned_data['name'] if form.cleaned_data['name'] != '' else None
        desc = form.cleaned_data['desc'] if form.cleaned_data['desc'] != '' else None

        self.model_scenario.xml = xml
        self.model_scenario.description = desc

        if name:
            self.model_scenario.name = name

        if submit_type == "run":
            simulation = submit.submit(self.request.user, xml)

            if simulation:
                self.model_scenario.simulation = simulation

        self.model_scenario.save()

        return super(ScenarioSummaryView, self).form_valid(form)
