########################################################################################################################
# VECNet CI - Prototype
# Date: 12/18/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################
from data_services.adapters.EMOD import EMOD_Adapter
from data_services.models import RunMetaData
from django.shortcuts import redirect
from django.views.generic import TemplateView
from lib.templatetags.base_extras import set_notification


class RunMetadataDetailView(TemplateView):
    """Class to implement single Run Metadata detail/edit view
    - Input: run ID
    - Output: HTML detail view of that run's metadata
    """
    template_name = 'ts_emod/run_metadata.html'

    def get_context_data(self, **kwargs):
        """Extension of get_context_data
            populate the existing metaData values
        """
        context = super(RunMetadataDetailView, self).get_context_data(**kwargs)
        the_request = self.request

        adapter = EMOD_Adapter(the_request.user.username)
        my_run = adapter.fetch_runs(run_id=int(kwargs['run_id']))

        # if we got here by edit URL, set edit mode.
        if 'mode' in kwargs.keys() and kwargs['mode'] == 'edit' and my_run.baseline_key.user.username == the_request.user.username:
            context['edit'] = True

        try:
            context['metaData'] = RunMetaData(my_run)
        except RuntimeError:
            set_notification('alert-error', '<strong>Error!</strong> Failed to retrieve metadata.', self.request.session)
            scenario_id = my_run.baseline_key
            if scenario_id:
                return redirect("ts_emod_scenario_details", scenario_id=str(scenario_id))
            else:
                return redirect("ts.index")

        return context

    def post(self, request, *args, **kwargs):
        """Handle the post of the edit form
        """
        my_form = request.POST
        adapter = EMOD_Adapter(request.user.username)
        my_run = adapter.fetch_runs(run_id=int(kwargs['run_id']))

        metaData = RunMetaData(my_run)
        changed_flag = 0

        for property, value in my_form.iteritems():
            if property in vars(metaData):
                setattr(metaData, property, value)
                changed_flag = 1

        # unchecked checkboxes do not register in the form
        #  so must set to off here if user unchecked is_public
        if 'is_public' not in my_form.keys() and metaData.is_public == 'on':
            setattr(metaData, 'is_public', 'off')
            changed_flag = 1

        # is user has made any changes, save it
        if changed_flag == 1:
            metaData.saveMetaData()

        return redirect("ts_emod_run_metadata_details", run_id=int(kwargs['run_id']))