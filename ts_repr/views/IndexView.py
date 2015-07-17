from django.views.generic import TemplateView

from data_services.models import DimUser


class IndexView(TemplateView):
    template_name = 'ts_repr/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'index'
        return context

    def post(self, request):
        #csvUploadForm = CsvUploadForm(prefix='csvUploadForm')
        a = 1