from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect
from django.views.generic import TemplateView

from data_services.models import DimUser
from lib.templatetags.base_extras import set_notification
from ts_emod2.models import Scenario, Location

import json


class SimulationUploaderView(TemplateView):
    template_name = "ts_emod2/simulation_uploader.html"

    def get_context_data(self, **kwargs):
        context = super(SimulationUploaderView, self).get_context_data(**kwargs)
        dim_user = DimUser.objects.get(username=self.request.user.username)
        context['dim_user'] = dim_user
        context['nav_button'] = 'simulation_uploader'

        public_locations = Location.objects.filter(user__isnull=True, deletion_timestamp__isnull=True)
        private_locations = Location.objects.filter(user=dim_user, deletion_timestamp__isnull=True)

        context['public_locations'] = public_locations
        context['private_locations'] = private_locations

        return context