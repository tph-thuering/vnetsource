########################################################################################################################
# VECNet CI - Prototype
# Date: 7/26/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
#   Gregory Davis <gdavis2@nd.edu>
########################################################################################################################
from data_services.adapters.EMOD import EMOD_Adapter
from django.views.generic import TemplateView
import ast
import re

class TemplateDetailView(TemplateView):
    """Class to implement single Scenario detail view

    - Input: scenario ID
    - Output: HTML detail view of that scenario
    """
    # TODO Consider additional comments

    template_name = 'ts_emod/template_detail.html'
    #template_name = 'ts_emod/scenario/browse_detail.html'

    def get_context_data(self, **kwargs):
        """Extension of get_context_data

        Add context data to drive detail view.
        """
        context = super(TemplateDetailView, self).get_context_data(**kwargs)
        context['selected_scenario'] = self.request.session['selected_scenario']
        adapter = EMOD_Adapter()

        my_template_id = kwargs['template_id']
        my_temp_list = adapter.fetch_template_list()
        for id in my_temp_list:
            if id == int(my_template_id):
                context['template_name'] = my_temp_list[id]['name']
                context['template_description'] = my_temp_list[id]['description']
                context['template_campaign_description'] = my_temp_list[id]['files']['campaign.json']['description']
                context['template_config_description'] = my_temp_list[id]['files']['config.json']['description']

                my_loc_list = adapter.fetch_locations()
                for loc_id in my_loc_list:
                    if loc_id == my_temp_list[id]['location_ndx']:
                        context['template_location_name'] = my_loc_list[loc_id]['place'] + ', ' + my_loc_list[loc_id]['country']
                        context['template_location_start_date'] = my_loc_list[loc_id]['start_date']
                        context['template_location_end_date'] = my_loc_list[loc_id]['end_date']
                        context['template_location_resolution'] = my_loc_list[loc_id]['resolution']
                        context['template_location_link'] = my_loc_list[loc_id]['link']

        my_temp = adapter.fetch_template(int(kwargs['template_id']))

        my_config = ast.literal_eval(my_temp['config.json'])
        context['template_campaign_warning'] = my_config['parameters']['Enable_Interventions']

        context['template_config'] = re.sub("\r{2,}", '\r', my_temp['config.json'])
        context['template_campaign'] = re.sub("\r{2,}", '\r', my_temp['campaign.json'])

        return context


