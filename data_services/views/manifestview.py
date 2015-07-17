"""
This is where the ManifestView class is stored and all related variables.
"""

import json
from django.views.generic import TemplateView
from data_services.manifestPreproc import manifest_preprocessor
from django.shortcuts import get_object_or_404
from data_services.models import DimRun
from django.http import HttpResponse, Http404


class ManifestView(TemplateView):
    """
    This view is responsible for displaying the manifest file as a JSON.  This will
    by used by the PSC cluster to pull the manifetss from the data warehouse.  This
    is a stop-gap measure used in preparation for Beta.  A more permanent solution in
    the form of the Shepherd script will be implemented after a successful Beta launch.
    """
    model_type = None

    def get_context_data(self, **kwargs):
        """
        This will put the JSON version of the manifest file into the context.
        """
        context = super(ManifestView, self).get_context_data(**kwargs)

        runID = kwargs['runID']
        run = get_object_or_404(
            DimRun,
            pk=runID
        )

        if len(run.dimexecution_set.all()) <= 0:
            raise Http404("Run %s has not been launched" % runID)

        manifest = manifest_preprocessor(run)

        context["manjson"] = manifest.as_json()

        return context

    def render_to_response(self, context, **response_kwargs):
        """
        This will render the response of this view as a JSON.
        """
        content = context["manjson"]
        return HttpResponse(content, content_type='application/octet-stream')