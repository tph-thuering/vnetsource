########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################
"""
This module contains the CubeView class.
"""

# import statements
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from datawarehouse.cubes_config import dwmodel
from datawarehouse.mixins import JSONMixin
from django.http import HttpResponse
from django.core.servers.basehttp import FileWrapper
from collections import OrderedDict
import json
import cStringIO

class CubeView(TemplateView):
    """Used to render the index page of the datawarehouse browser.

    This adds all available cube names to the context dictionary
    """
    #: Template used to render the datawarehouse browser index page
    template_name = 'datawarehouse/cube.html'
    test = None

    def get_context_data(self, **kwargs):
        """Extension of the get_context_data method of the Templateview.

        Used to add on the cube names to the context dictionary
        """
        context = super(CubeView, self).get_context_data(**kwargs)
        context['nav_button'] = 0

        if self.test:
            context['test'] = True
        else:
            context['test'] = False
        cube_dict = OrderedDict()                                       # create an empty dictionary to hold the cube names
        for cube in dwmodel.cubes:
            print str(cube)
            cube_dict[str(cube)] = str(dwmodel.cube(cube).label)          # add the cubes to the dictionary
        context['cube_dict'] = OrderedDict(sorted(cube_dict.items(), key=lambda x: x[1], reverse=False))  # add the cube list to the context
        return context                                                  # return the context


