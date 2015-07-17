########################################################################################################################
# VECNet CI - Prototype
# Date: 4/21/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################
"""
Admin interface for the TS EMOD
"""

from django.contrib import admin
from .models import *

admin.site.register(Intervention)
admin.site.register(Species)
admin.site.register(ConfigData)
