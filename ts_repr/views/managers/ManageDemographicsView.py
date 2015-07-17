from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView

from data_services.models import DimUser, SimulationInputFile
from lib.templatetags.base_extras import set_notification

from ts_repr.models import RepresentativeDemographics


class ManageDemographicsView(TemplateView):
    template_name = 'ts_repr/managers/manage_demographics.html'

    def get_context_data(self, **kwargs):
        context = super(ManageDemographicsView, self).get_context_data(**kwargs)
        context['dim_user'] = DimUser.objects.get_or_create(username=self.request.user.username)[0]
        context['nav_button'] = 'managers'
        context['current_manager'] = 'demographics'
        context['demographics_data_url'] = "/ts_repr/demographics/data/"

        context['active_demographics'] = RepresentativeDemographics.objects.filter(is_active=True).order_by('id')
        context['inactive_demographics'] = RepresentativeDemographics.objects.filter(is_active=False).order_by('id')

        return context

    def post(self, request):
        try:
            self.create_or_update_demographics_file(request)
        except Exception as exception:
            set_notification('alert-error', '<strong>Error!</strong> The entry may not have been saved! ' + str(exception), self.request.session)

        return HttpResponseRedirect(reverse('ts_repr.manage_demographics'))

    def create_or_update_demographics_file(self, request):
        username = "khostetl"
        metadata = {}

        demographics_id = int(request.POST['demographics_id'])
        name = request.POST['name']
        description = request.POST['description']
        demographics_type = request.POST['type']

        if 'is_active' in request.POST:
            is_active = True
        else:
            is_active = False

        if 'uncompiled_demographics' in request.FILES \
            and 'compiled_demographics' in request.FILES:
                are_files_here = True
        else:
            are_files_here = False

        demographics_file_location = request.POST['demographics_file_location']

        # 0 means we are explicitly requesting a new object, else we are looking for a specific one that supposedly
        # already exists, but if it doesn't, it will be created anyway
        if demographics_id == 0:
            demographics = RepresentativeDemographics(name=name,
                                                      description=description,
                                                      type=demographics_type,
                                                      is_active=is_active,
                                                      emod_demographics_compiled_file_location=demographics_file_location)
        else:
            try:  # Does exist, so modify with values from above
                demographics = RepresentativeDemographics.objects.get(id=demographics_id)
                demographics.name = name
                demographics.description = description
                demographics.type = demographics_type
                demographics.is_active = is_active
                demographics.emod_demographics_compiled_file_location = demographics_file_location
            except:  # Doesn't exist, so fill in with values from above
                demographics = RepresentativeDemographics(name=name,
                                                          description=description,
                                                          type=demographics_type,
                                                          is_active=is_active,
                                                          emod_demographics_compiled_file_location=demographics_file_location)

        uncompiled_demographics_file_name_short = "demographics.json"
        compiled_demographics_file_name_short = "demographics.compiled.json"

        if are_files_here:
            # Grab the contents from said files
            uncompiled_demographics_file_contents = request.FILES['uncompiled_demographics'].read()
            compiled_demographics_file_contents = request.FILES['compiled_demographics'].read()

            # Create the simulation input file for this uncompiled demographics file.
            uncompiled_demographics_simulation_file = SimulationInputFile.objects.create_file(
                contents=uncompiled_demographics_file_contents,
                name=uncompiled_demographics_file_name_short,
                metadata=metadata,
                created_by=DimUser.objects.get(username=username)
            )

            # Create the simulation input file for this compiled demographics file.
            compiled_demographics_simulation_file = SimulationInputFile.objects.create_file(
                contents=compiled_demographics_file_contents,
                name=compiled_demographics_file_name_short,
                metadata=metadata,
                created_by=DimUser.objects.get(username=username)
            )

            # Save the simulation input files
            uncompiled_demographics_simulation_file.save()
            compiled_demographics_simulation_file.save()

            # Add the file to the table
            demographics.emod_demographics = uncompiled_demographics_simulation_file
            demographics.emod_demographics_compiled = compiled_demographics_simulation_file

        demographics.save()

        set_notification('alert-success', '<strong>Success!</strong> Successfully saved.', self.request.session)