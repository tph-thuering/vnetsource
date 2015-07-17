from django.views.generic import TemplateView

from data_services.models import DimUser


class ManageOMSnippetView(TemplateView):
    template_name = 'ts_repr/managers/manage_om_snippet.html'

    def get_context_data(self, **kwargs):
        context = super(ManageOMSnippetView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'managers'
        context['current_manager'] = 'om_snippet'

        return context

    def post(self, request):
        #csvUploadForm = CsvUploadForm(prefix='csvUploadForm')
        a = 1