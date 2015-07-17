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
from django.core.urlresolvers import reverse
from django.views.generic import FormView

from ts_om.submit import submit
from ts_om.forms import StandaloneSubmitForm
from ts_om.models import Scenario

__author__ = 'Alexander'


class StandaloneSubmitView(FormView):
    template_name = "ts_om/standalone_submit_view.html"
    form_class = StandaloneSubmitForm
    xml = None
    scenario = None

    def get_success_url(self):
        return reverse('ts_om.list')

    def get_context_data(self, **kwargs):
        context = super(StandaloneSubmitView, self).get_context_data(**kwargs)
        context["left_menu_item"] = "standalone_submit_tool"

        return context

    def form_valid(self, form):
        name = form.cleaned_data['name']
        xml = form.cleaned_data['xml']
        model_version = form.cleaned_data['model_version']
        desc = form.cleaned_data['desc'] if form.cleaned_data['desc'] != '' else None

        scenario = Scenario(xml=xml, user=self.request.user, description=desc)
        if name:
            scenario.name = name
        scenario.save()
        simulation = submit(self.request.user.username, xml, model_version)
        scenario.simulation = simulation
        scenario.save()

        return super(StandaloneSubmitView, self).form_valid(form)
