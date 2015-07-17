########################################################################################################################
# VECNet CI - Prototype
# Date: 07/30/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

from data_services.data_api import EMODBaseline
from django.core.urlresolvers import reverse
from django.views.generic import FormView
import json

from ts_emod.forms import JsonEditForm


class JsonEditView(FormView):
    template_name = "ts_emod/json_edit.html"
    form_class = JsonEditForm

    def get_success_url(self):
        return reverse("ts_emod_scenario_details", kwargs={'scenario_id': self.kwargs['scenario_id']}) + '#' \
            + self.kwargs['file_type']

    def get_context_data(self, **kwargs):
        context = super(JsonEditView, self).get_context_data(**kwargs)

        if "scenario_id" in self.kwargs:
            scenario = EMODBaseline.from_dw(pk=self.kwargs["scenario_id"])

        context["scenario_id"] = scenario.id
        context["file_type"] = self.kwargs["file_type"]
        context["json"] = json.loads(json.dumps(scenario.get_file_by_type(self.kwargs["file_type"]).content.replace("u\'", "\'")))

        return context

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        scenario = EMODBaseline.from_dw(pk=self.kwargs["scenario_id"])

        my_type = self.kwargs["file_type"]
        scenario.add_file_from_string(my_type, my_type + '.json', str(form.cleaned_data['json']),
                                      description='Edited by User in JSON Editor')
        # update kwargs to detail page goes to new version of the scenario
        self.kwargs["scenario_id"] = scenario.id

        return super(JsonEditView, self).form_valid(form)