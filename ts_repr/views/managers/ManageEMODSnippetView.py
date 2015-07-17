from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from data_services.models import DimUser
from lib.templatetags.base_extras import set_notification

from ts_repr.models import RepresentativeSpecies, EMODSnippet

import json


class ManageEMODSnippetView(TemplateView):
    template_name = 'ts_repr/managers/manage_emod_snippet.html'

    def get_context_data(self, **kwargs):
        context = super(ManageEMODSnippetView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'managers'
        context['current_manager'] = 'emod_snippet'
        context['emod_snippet_data_url'] = "/ts_repr/emod_snippet/data/"

        context['snippets'] = EMODSnippet.objects.all().order_by('id')

        return context

    def post(self, request):
        try:
            self.create_or_update_emod_snippet(request)
        except Exception as exception:
            set_notification('alert-error', '<strong>Error!</strong> The entry may not have been saved! ' + str(exception), self.request.session)

        return HttpResponseRedirect(reverse('ts_repr.manage_emod_snippet'))

    def create_or_update_emod_snippet(self, request):
        # Information for the standard attributes. If a emod_snippet_id of 0 is specified, a new
        # EMODSnippet entry will be made using these values. If an already existing id is specified,
        # the current values will stay and these values will be ignored. However, if the id is not 0 and is not an
        # already existent entry, this will overwrite the current values with these values.
        emod_snippet_id = int(request.POST['emod_snippet_id'])
        name = request.POST['name']
        description = request.POST['description']
        snippet = request.POST['emod_snippet']

        # 0 means we are explicitly requesting a new object, else we are looking for a specific one that supposedly
        # already exists, but if it doesn't, it will be created anyway
        if emod_snippet_id == 0:
            emod_snippet = EMODSnippet(name=name, description=description, snippet=snippet)
        else:
            try:  # Does exist, so use current values
                emod_snippet = EMODSnippet.objects.get(id=emod_snippet_id)
                emod_snippet.name = name
                emod_snippet.description = description
                emod_snippet.snippet = snippet
            except:  # Doesn't exist, so fill in with values from above
                emod_snippet = EMODSnippet(name=name, description=description, snippet=snippet)

        emod_snippet.save()

        if 'Sporozoite_Rate' in json.loads(snippet)[name]:
            set_notification('alert-success', '<strong>Success!</strong> Successfully saved.', self.request.session)
        else:
            set_notification('alert-error', '<strong>Success with warning!</strong> Successfully saved, however Sporozoite_Rate was not added!', self.request.session)