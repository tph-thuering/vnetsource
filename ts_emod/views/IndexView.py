########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################

# Imports that are external to the ts_emod app

from django.views.generic import TemplateView


## An extension of TemplateView to function as home page.
#
# Sets template and adds nav menu context.
class IndexView(TemplateView):
    template_name = 'ts_emod/index.html'

    ## Extension of the get_context_data method of the Templateview.
    #
    #  Sets "nav_button" to 0 so nav menu selected-indicator highlights.
    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['nav_button'] = "index"
        return context
