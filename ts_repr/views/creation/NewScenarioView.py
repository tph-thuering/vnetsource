from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from data_services.models import DimUser, DimTemplate, DimModel, DimBaseline
from data_services.adapters import EMOD_Adapter
from data_services.data_api import EMODBaseline

import json
from ts_repr.utils.misc_functions import BEGIN_STEP

step_number = BEGIN_STEP


class NewScenarioView(TemplateView):
    template_name = 'ts_repr/creation/new_scenario.html'

    def get_context_data(self, **kwargs):
        context = super(NewScenarioView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        print self.request.user.username
        print DimUser.objects.get_or_create(username=self.request.user.username)[0].username == ''
        context['nav_button'] = 'new_scenario'
        context['current_step'] = 'name'
        context['page_name'] = 'new'
        context['can_use_just_save'] = False

        return context

    def post(self, request):
        scenario_id = self.save_new_scenario_data(request)

        return HttpResponseRedirect(reverse('ts_repr.weather', kwargs={'scenario_id': scenario_id}))

    def save_new_scenario_data(self, request):
        # Create initial scenario
        # Create initial scenario
        # Create initial scenario
        adapter = EMOD_Adapter(request.user.username)

        emod_scenario = EMODBaseline(
            name='',
            description='Made with representative workflow',
            model=DimModel.objects.get(model='EMOD'),
            user=DimUser.objects.get_or_create(username=request.user.username)[0]
        )

        template_object = DimTemplate.objects.get(template_name="Representative Location")

        emod_scenario.model_version = template_object.model_version
        emod_scenario.template_id = 21
        emod_scenario.template = template_object

        # Create and add a config file
        config_json = json.loads(template_object.get_file_content('config.json'))
        emod_scenario.add_file_from_string('config', 'config.json', json.dumps(config_json), description='SOMETHING')

        # populate campaign
        try:
            campaign = json.loads(template_object.get_file_content('campaign.json'))
        except KeyError:
            # use empty campaign file
            campaign = json.loads({"Events": []})

        # Add the emod_scenario campaign file
        emod_scenario.add_file_from_string('campaign', 'campaign.json', json.dumps(campaign), description='SOMETHING')

        emod_scenario.save()
        # Create initial scenario
        # Create initial scenario
        # Create initial scenario

        # Hack until I know how to retrieve files from DimBaseline without funneling it through EMODBaseline
        dim_scenario = DimBaseline.objects.get(id=emod_scenario.id)

        # Add metadata
        current_metadata = {}
        current_metadata['representative'] = {}

        # Fill data
        current_metadata['representative']['steps_complete'] = step_number + 1
        current_metadata['representative']['is_complete'] = False
        current_metadata['representative']['is_editable'] = True
        dim_scenario.metadata = json.dumps(current_metadata)

        dim_scenario.save()

        print "Scenario ID = " + str(emod_scenario.id)

        return emod_scenario.id