# PEP 0263
# -*- coding: utf-8 -*-
########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Alexander Vyushkov <Alexander.Vyushkov@nd.edu>
########################################################################################################################

from django.views.generic import TemplateView

__author__ = 'Alexander'


class IndexView(TemplateView):
    """
    Main page for the OpenMalaria Prototype UIs
    Renders a given template specified in template_name below, passing it a {{ params }} template variable,
    which is a dictionary of the parameters captured in the URL and modified by get_context_data.
    """
    template_name = 'ts_om/index.html'

    def get_context_data(self, **kwargs):
        """
        Return a context data dictionary consisting of the contents of kwargs stored in the context variable params.
        """
        # Required by any Django view
        context = super(IndexView, self).get_context_data()
        # Return context data
        return context
