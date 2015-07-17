from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = 'ts_emod2/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['nav_button'] = 'index'

        return context