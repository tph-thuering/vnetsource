# PEP 0263
# -*- coding: utf-8 -*-
########################################################################################################################
# VECNet CI - Prototype
# Date: 04/10/2015
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <rjones29@nd.edu>
########################################################################################################################
# Cloned from IndexView.py

from django.views.generic import TemplateView
import transmission_simulator


class RepresentativeView(TemplateView):
    """
    Main page for the Transmission Simulator
    Renders a given template specified in template_name below, passing it a {{ params }} template variable,
    which is a dictionary of the parameters captured in the URL and modified by get_context_data.
    """
    template_name = 'transmission_simulator/representative.html'

    def get_context_data(self, **kwargs):
        """
        Return a context data dictionary consisting of the contents of kwargs stored in the context variable params.
        """
        # Required by any Django view
        context = super(RepresentativeView, self).get_context_data()
        # Add TS version to the {{ params }} template variable
        # TS version is to be displayed in the page title
        context['version'] = "v" + transmission_simulator.__version__

        # set flag for nav menu activation
        context['nav_button'] = 'representative'

        # Return context data
        return context