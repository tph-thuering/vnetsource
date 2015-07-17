########################################################################################################################
# VECNet CI - Prototype
# Date: 03/07/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################
from django.db.models import Q
from data_services.adapters.EMOD import EMOD_Adapter
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from data_services.models import DimBaseline, DimRun, DimUser

from django.utils.decorators import method_decorator
from django.views.generic import ListView

import json


class ScenarioBrowsePublicView(ListView):
    """Class to implement Run list view

    - Output: HTML detail view of all "available" scenarios based on is_public and user id/created_by
    """
    model = DimBaseline
    queryset = DimBaseline.objects.filter(Q(is_deleted=False) & Q(is_public=True)).order_by('-id')
    template_name = 'ts_emod/scenario/scenario_browse_public.html'

    # @method_decorator(login_required)  # not needed for Public run list
    def dispatch(self, request, *args, **kwargs):
        """
        Accepts a request argument plus arguments, and returns a HTTP response.
        """
        return super(ScenarioBrowsePublicView, self).dispatch(request, *args, **kwargs)

    # def get_queryset(self):
    #     """
    #     This view returns a list of all the scenarios
    #     for the currently authenticated user.
    #     """
    #     queryset = super(ScenarioBrowsePublicView, self).get_queryset()
    #     queryset = queryset.filter(user_key=1, is_deleted=False)
    #     return queryset

    def get_context_data(self, **kwargs):
        """Extension of get_context_data

        Add context data to drive menu nav highlights, breadcrumbs and pagers.
        """
        context = super(ScenarioBrowsePublicView, self).get_context_data(**kwargs)
        the_request = self.request

        context['nav_button'] = 'scenario_browse_public'

        if context['object_list'] is None:
            return context

        pager_size = the_request.POST.get('pager_size') or the_request.GET.get('pager_size')
        if pager_size is None:
            pager_size = 10
        else:
            pager_size = int(pager_size)

        paginator = Paginator(context['object_list'], pager_size)
        page = int(the_request.GET.get('page') or 1)
        try:
            scenario_list = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            scenario_list = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            scenario_list = paginator.page(paginator.num_pages)

        scenario_count = paginator.count
        context['pager_size'] = pager_size
        context['scenario_list'] = scenario_list.object_list
        context['pager_obj'] = scenario_list
        context['scenario_range'] = range(paginator.num_pages)
        context['scenario_count'] = scenario_count
        context['current_start'] = (page-1)*pager_size + 1
        context['current_stop'] = min(scenario_count, (page-1)*pager_size + pager_size)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]

        adapter = EMOD_Adapter(self.request.user.username)

        for scenario in context['scenario_list']:
            run_list = DimRun.objects.filter(baseline_key=scenario.id).order_by('-id')
            scenario.run_list = run_list
            scenario.run_count = len(run_list)
            scenario.run_id = 0  # set a dummy id
            my_model_version = ''

            # get status for each run
            for run in run_list:
                status = adapter.run_status(run.id)
                if status is None:
                    run.my_completed = "No"
                else:
                    run.my_completed = status[0]
                    run.my_failed = status[2]
                    if int(status[0]) > 0:
                        scenario.run_id = run.id
                        scenario.run_name = run.name
                        scenario.location_key = run.location_key
                            #break
                my_model_version = run.model_version

            try:
                scenario.model_version = scenario.my_scenario.my_model_version
            except (AttributeError, ObjectDoesNotExist):
                scenario.model_version = my_model_version

        return context