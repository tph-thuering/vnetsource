########################################################################################################################
# VECNet CI - Prototype
# Date: 01/23/2015
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

from data_services.adapters.EMOD import EMOD_Adapter
from data_services.models import DimRun, RunMetaData, DimBaseline, DimUser
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView
import json
from lib.templatetags.base_extras import set_notification


class MetadataView(TemplateView):
    """
    Returns a JSON file containing metadata.
    - if a run id is provided, the file will contain only the metadata for this run
    - else the file will contain the metadata for all public runs

    input: Run Id (optional)
    output: JSON file
    """
    model_type = None

    def get_context_data(self, **kwargs):
        """
        This will put the metadata (as JSON) into the context.
        """
        context = super(MetadataView, self).get_context_data(**kwargs)

        if 'runID' in kwargs.keys():
            runID = kwargs['runID']
            my_run = get_object_or_404(
                DimRun,
                pk=runID
            )

            try:
                metadata = RunMetaData(my_run)
            except RuntimeError as error:
                set_notification('alert-error', '<strong>Error!</strong> Failed to load metadata. ' +
                                 str(error), self.request.session)
                return redirect("ts.index")
            metadata.getMetaData_as_JSON()
            context['metaDataJSON'] = {runID: metadata.as_json}
        else:
            context['metaDataJSON'] = {}
            adapter = EMOD_Adapter(self.request.user.username)
            # get list of public scenarios
            public_user = DimUser.objects.get(id=1)
            queryset = DimBaseline.objects.filter(user=public_user, is_deleted=False).order_by('-id')
            for scenario in queryset:
                # for each public exp, get list of runs
                run_list = adapter.fetch_runs(scenario_id=scenario.id, as_object=True)

                # for each run, append the metadata
                for my_run in run_list:
                    if my_run.jcd is not None:
                        metadata = RunMetaData(my_run)
                        metadata.getMetaData_as_JSON()
                        context['metaDataJSON'].update({my_run.id: metadata.as_json})

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        This will render the response of this view as a JSON file.
        """
        return HttpResponse(json.dumps(context["metaDataJSON"]), mimetype='application/json')