########################################################################################################################
# VECNet CI - Prototype
# Date: 05/05/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app

from django import forms

# Imports that are internal to the ts_emod app

from ts_emod.forms import CustomForm
from ts_emod.fields import UnValidatedMultipleChoiceField


class SweepToolSweepForm(CustomForm):
    """ A class representing the Sweep selection step in the SweepToolSweepForm.

    This displays the sweeps and
    allows the user to select one or more from the list.
    """
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':
                                                         'Name this sweep configuration',
                                                  'required': ''}))
    sweeps = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())
    values = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())

    def __init__(self, *args, **kwargs):
        super(SweepToolSweepForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            if key in ['sweep']:
                self.fields[key].required = False

    def clean(self):
        """ Custom clean method: replace commas with "|" characters for individual value sweeps (not $ nodes/chunks) """

        cleaned_data = super(SweepToolSweepForm, self).clean()
        try:
            for i in range(len(dict(self.data)['sweep-values'])):
                if "$" not in dict(self.data)['sweep-values'][i]:
                    dict(self.data)['sweep-values'][i] = \
                        dict(self.data)['sweep-values'][i].replace(',', '|').replace(" ", "")
        except KeyError:
            pass
        return cleaned_data

#: A tuple assigning step names to corresponding Forms
#:
#: Used in SweepToolView
named_sweep_tool_forms = (
    ('sweep', SweepToolSweepForm),
)
