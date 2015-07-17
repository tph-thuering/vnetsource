########################################################################################################################
# VECNet CI - Prototype
# Date: 6/18/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app
from django.forms import HiddenInput

# Imports that are internal to the ts_emod app
from ts_emod.forms import CustomModelForm
from ts_emod.models import ConfigData
from ts_emod.fields import JSONConfigWidget, JSONConfigWidgetTwoColumn


class SpeciesCreateForm(CustomModelForm):
    """A class to override the default ModelForm Meta

    Sets the model to ConfigData and sets unneeded field widgets to hidden.
    """
    class Meta:
        model = ConfigData
        widgets = {
            'name': HiddenInput,
            'description': HiddenInput,
            'type': HiddenInput,
            'misc': HiddenInput,
            'json': JSONConfigWidget}


class SpeciesCreateTwoColumnForm(CustomModelForm):
    """A class to override the default ModelForm Meta

    Sets the model to ConfigData and sets unneeded field widgets to hidden.
    """
    class Meta:
        model = ConfigData
        widgets = {
            'name': HiddenInput,
            'description': HiddenInput,
            'type': HiddenInput,
            'misc': HiddenInput,
            'json': JSONConfigWidgetTwoColumn}
