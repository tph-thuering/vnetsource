from functools import partial, wraps
import json
from xml.etree.ElementTree import ParseError

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms.formsets import formset_factory
from vecnet.openmalaria.scenario import Scenario

from ts_om.models import Scenario as ScenarioModel
from ts_om.forms import ScenarioDeploymentsForm, ScenarioDeploymentForm
from ts_om.views.ScenarioBaseFormView import ScenarioBaseFormView
from ts_om.views.ScenarioValidationView import rest_validate

__author__ = 'nreed'


class ScenarioDeploymentsView(ScenarioBaseFormView):
    template_name = "ts_om/deployments.html"
    form_class = ScenarioDeploymentsForm

    def get_success_url(self):
        return reverse('ts_om.summary', kwargs={'scenario_id': self.kwargs['scenario_id']})

    def get_context_data(self, **kwargs):
        context = super(ScenarioDeploymentsView, self).get_context_data(**kwargs)

        component_ids = []
        for intervention in self.scenario.interventions.human:
            component_ids.append((intervention.id, intervention.id))

        ScenarioDeploymentFormSet = formset_factory(wraps(ScenarioDeploymentForm)
                                                    (partial(ScenarioDeploymentForm, components=component_ids)),
                                                    extra=0, can_delete=True)
        deployment_formset = ScenarioDeploymentFormSet(initial=parse_deployments(self.scenario),
                                                       prefix='deployment')

        context["deployment_formset"] = deployment_formset
        context["has_components"] = len(component_ids) > 0

        return context

    def form_valid(self, form, **kwargs):
        component_ids = []
        for intervention in self.scenario.interventions.human:
            component_ids.append((intervention.id, intervention.id))

        ScenarioDeploymentFormSet = formset_factory(wraps(ScenarioDeploymentForm)
                                                    (partial(ScenarioDeploymentForm, components=component_ids)),
                                                    extra=0, can_delete=True)
        deployment_formset = ScenarioDeploymentFormSet(self.request.POST, prefix='deployment')

        if not deployment_formset.is_valid():
            return super(ScenarioDeploymentsView, self).form_invalid(form)

        deployments = []
        for form in deployment_formset:
            deployment_info = {
                'name': '',
                'components': form.cleaned_data["components"]
            }

            if 'name' in form.cleaned_data:
                deployment_info['name'] = form.cleaned_data["name"]

            times = form.cleaned_data["timesteps"].split(',')
            coverages = form.cleaned_data["coverages"].split(',')
            timesteps = []
            for index, time in enumerate(times):
                timesteps.append({
                    "time": time,
                    "coverage": coverages[index] if len(coverages) > index else coverages[0]
                })

            deployment_info["timesteps"] = timesteps
            deployments.append(deployment_info)

        self.scenario.interventions.human.deployments = deployments

        return super(ScenarioDeploymentsView, self).form_valid(form, kwargs={'xml': self.scenario.xml})


def parse_deployments(scenario):
    deployments = []

    for deployment in scenario.interventions.human.deployments:
        deployment_info = {'name': deployment.name, 'components': deployment.components}

        times = [str(timestep["time"]) for timestep in deployment.timesteps]
        coverages = [str(timestep["coverage"]) for timestep in deployment.timesteps]

        deployment_info["timesteps"] = ','.join(times)
        deployment_info["coverages"] = ','.join(coverages)

        deployments.append(deployment_info)

    return deployments
