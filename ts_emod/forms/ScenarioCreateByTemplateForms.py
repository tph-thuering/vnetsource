########################################################################################################################
# VECNet CI - Prototype
# Date: 01/27/2015
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app
from django import forms
from django.utils.safestring import mark_safe

# Imports that are internal to the ts_emod app
from ts_emod.forms import CustomForm


class LocationForm(CustomForm):
    """A class representing the location feedback step in the BaselineWizardView.

    This displays graphs of the user-selected location data for the user to review.
    """
    template_id = forms.IntegerField()
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Type in a short name for the simulation',
                                                         'required': ''}))
    description = forms.CharField(help_text=mark_safe('<span class="helptext-narrow">Characters '
                                                      'remaining: <span id="count"></span></span>'),
                                  widget=forms.Textarea(attrs={'class': 'description-box',
                                  'placeholder': 'Type in a short description of the simulation'}))

    def __init__(self, *args, **kwargs):
        super(LocationForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            if key in ['description']:
                self.fields[key].required = False

#: A tuple assigning step names to corresponding Forms
#:
#: Used in BaselineWizardView
named_scenarioCreateByTemplate_forms = (
    ('location', LocationForm),
)
