########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################
from django.views.generic import TemplateView

class IndexView(TemplateView):
    template_name = 'lib/index.html'
