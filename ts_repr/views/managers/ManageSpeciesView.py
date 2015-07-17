from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from data_services.models import DimUser
from lib.templatetags.base_extras import set_notification

from ts_repr.models import RepresentativeSpecies, EMODSnippet, OMSnippet, RepresentativeSpeciesHabitatType

import json


class ManageSpeciesView(TemplateView):
    template_name = 'ts_repr/managers/manage_species.html'

    def get_context_data(self, **kwargs):
        context = super(ManageSpeciesView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'managers'
        context['current_manager'] = 'species'
        context['species_data_url'] = "/ts_repr/species/data/"
        context['emod_snippet_data_url'] = "/ts_repr/emod_snippet/data/"
        context['om_snippet_data_url'] = "/ts_repr/om_snippet/data/"

        context['active_species'] = RepresentativeSpecies.objects.filter(is_active=True).order_by('id')
        context['inactive_species'] = RepresentativeSpecies.objects.filter(is_active=False).order_by('id')

        context['emod_snippets'] = EMODSnippet.objects.filter().order_by('id')
        context['om_snippets'] = OMSnippet.objects.filter().order_by('id')

        return context

    def post(self, request):
        try:
            self.create_or_update_species(request)
        except Exception as exception:
            set_notification('alert-error', '<strong>Error!</strong> The entry may not have been saved! ' + str(exception), self.request.session)

        return HttpResponseRedirect(reverse('ts_repr.manage_species'))

    def create_or_update_species(self, request):
        # Information for the standard attributes. If a species_id of 0 is specified, a new
        # RepresentativeSpecies entry will be made using these values. If an already existing id is specified,
        # the current values will stay and these values will be ignored. However, if the id is not 0 and is not an
        # already existent entry, this will overwrite the current values with these values.
        species_id = int(request.POST['species_id'])
        name = request.POST['name']
        description = request.POST['description']
        emod_snippet_id = int(request.POST['emod_snippet_id'])  # If 0 then null.
        om_snippet_id = int(request.POST['om_snippet_id'])  # If 0 then null.

        if 'is_active' in request.POST:
            is_active = True
        else:
            is_active = False

        # 0 means we are explicitly requesting a new object, else we are looking for a specific one that supposedly
        # already exists, but if it doesn't, it will be created anyway
        if species_id == 0:
            species = RepresentativeSpecies(name=name,
                                            description=description,
                                            habitat_type=RepresentativeSpeciesHabitatType.objects.get(id=1),
                                            is_active=is_active)
        else:
            try:  # Does exist, so use current values
                species = RepresentativeSpecies.objects.get(id=species_id)
                species.name = name
                species.description = description
                species.is_active = is_active
            except:  # Doesn't exist, so fill in with values from above
                species = RepresentativeSpecies(name=name,
                                                description=description,
                                                habitat_type=RepresentativeSpeciesHabitatType.objects.get(id=1),
                                                is_active=is_active)

        if emod_snippet_id != 0:
            try:
                species.emod_snippet = EMODSnippet.objects.get(id=emod_snippet_id)
            except:
                print 'EMOD snippet with id ' + str(emod_snippet_id) + ' does not exist!'
                raise ValueError('Error')
        else:
            print emod_snippet_id
            raise ValueError('Error')

        if om_snippet_id != 0:
            try:
                species.om_snippet = OMSnippet.objects.get(id=om_snippet_id)
            except:
                print 'OM snippet with id ' + str(om_snippet_id) + ' does not exist!'

        species.save()
        set_notification('alert-success', '<strong>Success!</strong> Successfully saved.', self.request.session)