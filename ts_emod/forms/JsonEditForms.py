########################################################################################################################
# VECNet CI - Prototype
# Date: 07/30/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

from django import forms

class JsonEditForm(forms.Form):
    json = forms.CharField(widget=forms.Textarea)
