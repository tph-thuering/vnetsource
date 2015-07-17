from django.views.generic import TemplateView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from data_services.models import DimUser

from ts_repr.models import RepresentativeScenario


class BrowseScenarioView(TemplateView):
    template_name = 'ts_repr/browse_scenario.html'

    def get_context_data(self, **kwargs):
        context = super(BrowseScenarioView, self).get_context_data(**kwargs)
        dim_user = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['dim_user'] = dim_user
        context['nav_button'] = 'browse_scenario'

        pager_size = self.request.POST.get('pager_size') or self.request.GET.get('pager_size')

        if pager_size is None:
            pager_size = 10
        else:
            pager_size = int(pager_size)

        type_currently_shown = self.request.POST.get('type') or self.request.GET.get('type')

        print type_currently_shown
        if type_currently_shown is None:
            type_currently_shown = "Incomplete"

        if type_currently_shown == "Incomplete":
            is_completed = False
        elif type_currently_shown == "Complete":
            is_completed = True
        else:
            raise ValueError("type_currently_shown is set to " + type_currently_shown + " which is invalid.")

        all_scenarios = RepresentativeScenario.objects.filter(is_deleted=False,
                                                              is_completed=is_completed,
                                                              user=dim_user).order_by('-id')
        number_of_representative_scenarios = len(all_scenarios)

        paginator = Paginator(all_scenarios, pager_size)
        page = int(self.request.GET.get('page') or 1)

        try:
            representative_scenarios = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            representative_scenarios = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            representative_scenarios = paginator.page(paginator.num_pages)

        context['pager_size'] = pager_size
        context['page'] = page
        context['representative_scenarios'] = representative_scenarios
        context['number_of_representative_scenarios'] = number_of_representative_scenarios
        context['scenario_range'] = range(paginator.num_pages)
        context['current_start'] = (page-1) * pager_size + 1
        context['current_stop'] = min(number_of_representative_scenarios, (page-1) * pager_size + pager_size)
        context['type_currently_shown'] = type_currently_shown

        return context

    # Add context to posting
    def post(self, request, **kwargs):
        context = self.get_context_data()
        return self.render_to_response(context)