########################################################################################################################
# VECNet CI - Prototype
# Date: 04/23/2014
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app

from django import forms

# Imports that are internal to the ts_emod app

from ts_emod.forms import CustomForm


class LaunchStartForm(CustomForm):
    """A class representing the start step in the LaunchWizard.
    """
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Type in a short name for the run.',
                                                         'required': ''}))

    choices_cluster = [(1, 'Cluster at ND')] #, (2, 'Not yet available: Full VecNet Cluster at ND')]
                       # (3, 'Not yet available: BOINC')]
    cluster_type = forms.ChoiceField(label='Run on', widget=forms.Select(), choices=choices_cluster)

    #5853 - temporarily hide this, apparently it's not using different random seeds for each rep anyway...
    #choices = [(1, 1), (3, 3), (5, 5)]
    #reps_per_exec = forms.ChoiceField(label='Repetitions', widget=forms.Select(), choices=choices)
    # Line below caused an issue with form's .as_grid_div so I set done method to use 1
    #reps_per_exec = forms.ChoiceField(label="", widget=forms.HiddenInput(attrs={'value': 1}), choices=choices)

#: A tuple assigning step names to corresponding Forms
#:
#: Used in LaunchTool
named_launch_tool_forms = (
    ('start', LaunchStartForm),
    #('destination', LaunchDefineCluster),  # Put both selectors on same page
)
