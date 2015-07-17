from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from data_services.models import DimUser

from ts_repr.models import RepresentativeSpeciesParameter


class ManageSpeciesParameterView(TemplateView):
    template_name = 'ts_repr/managers/manage_species_parameter.html'

    def get_context_data(self, **kwargs):
        context = super(ManageSpeciesParameterView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'managers'
        context['current_manager'] = 'species_parameter'

        return context

    def post(self, request):
        self.create_species_parameter(request)
        # Just some place to go for now to visually see that this is posting
        return HttpResponseRedirect(reverse('ts_repr.manage_model_version'))

    def create_species_parameter(self, request):
        main_path = "Z:/winhpc_scripts/input16/repr/"

        # Information for the standard attributes. If a species_parameter_id of 0 is specified, a new
        # RepresentativeSpeciesParameter entry will be made using these values. If a already existing id is specified,
        # the current values will stay and these values will be ignored. However, if the id is not 0 and is not an
        # already existent entry, this will overwrite the current values with these values.
        species_parameter_id = 1
        name = "Example"
        description = "Example"
        emod_high = 999
        emod_medium = 888
        emod_low = 777
        om_high = 999
        om_medium = 888
        om_low = 777
        is_active = True

        # 0 means we are explicitly requesting a new object, else we are looking for a specific one that supposedly
        # already exists, but if it doesn't, it will be created anyway
        if species_parameter_id == 0:
            species_parameter = RepresentativeSpeciesParameter.objects.create(name=name,
                                                                              description=description,
                                                                              emod_high=emod_high,
                                                                              emod_medium=emod_medium,
                                                                              emod_low=emod_low,
                                                                              om_high=om_high,
                                                                              om_medium=om_medium,
                                                                              om_low=om_low,
                                                                              is_active=is_active)
        else:
            try:  # Does exist, so use current values
                species_parameter = RepresentativeSpeciesParameter.objects.get(id=species_parameter_id)
            except:  # Doesn't exist, so fill in with values from above
                species_parameter = RepresentativeSpeciesParameter.objects.create(name=name,
                                                                                  description=description,
                                                                                  emod_high=emod_high,
                                                                                  emod_medium=emod_medium,
                                                                                  emod_low=emod_low,
                                                                                  om_high=om_high,
                                                                                  om_medium=om_medium,
                                                                                  om_low=om_low,
                                                                                  is_active=is_active)

        species_parameter.save()