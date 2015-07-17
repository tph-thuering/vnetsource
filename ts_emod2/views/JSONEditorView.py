from django.shortcuts import redirect
from django.views.generic import TemplateView

from data_services.models import DimUser
from lib.templatetags.base_extras import set_notification
from ts_emod2.models import Scenario

import json


class JSONEditorView(TemplateView):
    template_name = "ts_emod2/json_editor.html"

    def get_context_data(self, **kwargs):
        context = super(JSONEditorView, self).get_context_data(**kwargs)

        dim_user = DimUser.objects.get(username=self.request.user.username)
        file_type = kwargs['file_type']
        scenario = Scenario.objects.get(id=kwargs['scenario_id'])

        context['file_type'] = file_type
        context['scenario'] = scenario
        context['json'] = scenario.get_file_by_type(file_type).get_contents()

        print context['json']

        return context

    def post(self, request, file_type, scenario_id):
        dim_user = DimUser.objects.get(username=request.user.username)
        scenario = Scenario.objects.get(id=scenario_id)

        try:
            if 'json' in request.POST:
                try:
                    print request.POST['json']
                    the_json = json.loads(request.POST['json'])
                except:
                    raise RuntimeError("Bad json.")
            else:
                raise ValueError("Json is not in the post.")

            contents = json.dumps(the_json, indent=4, separators=(',', ': '))

            scenario.set_file_by_type(file_type, contents)
            set_notification('alert-success', '<strong>Success!</strong> Saved new json.', request.session)
        except RuntimeError as error:
            set_notification('alert-error', '<strong>Error!</strong> Failed to save json. ' + str(error), request.session)

        return redirect("ts_emod2.details", scenario_id=scenario.id)