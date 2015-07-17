from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import redirect
from django.views.generic import TemplateView

from data_services.models import DimUser
from lib.templatetags.base_extras import set_notification
from ts_emod2.models import Scenario as EMODScenario
from ts_om.models import Scenario as OMScenario

import json


class PublicSimulationsView(TemplateView):
    template_name = "ts_emod2/public_simulations.html"

    def get_context_data(self, **kwargs):
        context = super(PublicSimulationsView, self).get_context_data(**kwargs)
        dim_user = DimUser.objects.get(username=self.request.user.username)
        context['dim_user'] = dim_user
        context['nav_button'] = 'public_simulations'

        pager_size = self.request.POST.get('pager_size') or self.request.GET.get('pager_size')

        if pager_size is None:
            pager_size = 10
        else:
            pager_size = int(pager_size)

        type_currently_shown = self.request.POST.get('type') or self.request.GET.get('type')

        print type_currently_shown
        if type_currently_shown is None:
            type_currently_shown = "All"

        if type_currently_shown != "All" and type_currently_shown != "EMOD" and type_currently_shown != "OM":
            raise ValueError("type_currently_shown is set to " + type_currently_shown + " which is invalid.")

        if type_currently_shown == 'All' or type_currently_shown == 'EMOD':
            emod_scenarios = EMODScenario.objects.filter(deletion_timestamp__isnull=True, is_public=True).order_by('-id')
        else:
            emod_scenarios = None

        for scenario in emod_scenarios:
            if scenario.extra_metadata:
                if 'representative' in scenario.extra_metadata:
                    scenario.is_representative = True
            scenario.is_emod = True

        # if type_currently_shown == 'All' or type_currently_shown == 'OM':
        #     om_scenarios = EMODScenario.objects.filter(deleted=False, user=dim_user).order_by('-id')
        # else:
        #     om_scenarios = None

        all_scenarios = emod_scenarios  #+ om_scenarios

        number_of_scenarios = len(all_scenarios)

        paginator = Paginator(all_scenarios, pager_size)
        page = int(self.request.GET.get('page') or 1)

        try:
            scenarios = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            scenarios = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            scenarios = paginator.page(paginator.num_pages)

        context['pager_size'] = pager_size
        context['page'] = page
        context['scenarios'] = scenarios
        context['number_of_scenarios'] = number_of_scenarios
        context['scenario_range'] = range(paginator.num_pages)
        context['current_start'] = (page-1) * pager_size + 1
        context['current_stop'] = min(number_of_scenarios, (page-1) * pager_size + pager_size)
        context['type_currently_shown'] = type_currently_shown

        return context