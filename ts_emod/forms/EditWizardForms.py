########################################################################################################################
# VECNet CI - Prototype
# Date: 01/16/2015
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

# Imports that are external to the ts_emod app

from data_services.adapters.EMOD import EMOD_Adapter
from django import forms
from django.forms import HiddenInput
from django.utils.safestring import mark_safe

# Imports that are internal to the ts_emod app

from ts_emod.fields import UnValidatedMultipleChoiceField, JSONConfigWidget
from ts_emod.forms import CustomForm, CustomModelForm
from ts_emod.models import ConfigData


class EditRunForm(CustomForm):
    """A class representing the run step in the EditWizardView.
    """
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Type in a short name for the test run',
                                                         'required': ''}))


class EditClimateForm(CustomForm):
    """A class representing the location step in the EditWizardView.

    This list represents the files sets to be used in simulations.
    """


class EditDemographicForm(CustomForm):
    """A class representing the location feedback step in the EditWizardView.

    This displays graphs of the user-selected location data for the user to review.
    """
    #class Meta:
    #    widgets = {'placeholder': HiddenInput}


class EditConfigForm(CustomForm):
    """A class representing the config step in the EditWizardView.

    This allows the user to specify the date-range of climate data to use in the simulation.
    """
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Type in a short name for the simulation',
                                                         'required': ''}))
    description = forms.CharField(help_text=mark_safe('<span class="helptext-narrow">Characters '
                                                      'remaining: <span id="count"></span></span>'),
                                  widget=forms.Textarea(attrs={'class': 'description-box',
                                  'placeholder': 'Type in a short description of the simulation'}))

    #: Specify the start and end of the date range
    #Start_Time = forms.IntegerField(widget=forms.TextInput(attrs={'style': "width: 60px"}))
    Start_Time = forms.IntegerField(widget=HiddenInput)
    # widget=forms.TextInput(attrs={'id':'start_date', 'style':"border: 1;
    # color: #f6931f; font-weight: bold; width: 30px"}))
    # end_date = forms.IntegerField(label='End Dec 31 of Year:',
    # widget=forms.TextInput(attrs={'id':'end_date', 'style':"border: 1;
    # color: #f6931f; font-weight: bold; width: 30px"}))
    Simulation_Duration = forms.IntegerField(widget=forms.TextInput(attrs={'style': "width: 60px"}))

    CHOICES = [('VECTOR_SIM', 'Vector Simulation'),
               ('MALARIA_SIM', 'Malaria Simulation')]

    Simulation_Type = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect())

    def __init__(self, *args, **kwargs):
        super(EditConfigForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            if key in ['description']:
                self.fields[key].required = False

    def as_grid_div(self):
        """Override as_grid_div method to provide different span spacing in Template

        Returns this form rendered as HTML::

            <div class=span2/1/1>s -- excluding the <div class=row></div>."
        """
        return self._html_output(
            normal_row='<div class="span2">%(label)s</div>%(field)s%(help_text)s',
            error_row='<div class="row"><div class="span8">%s</div></div>',
            row_ender='</div><div class="row">',
            help_text_html='<span class="helptext">%s</span>',
            errors_on_separate_row=True)

    def as_insert_slider_div(self):

        output = []
        for name, field in self.fields.items():
            bf = self[name]
            output.append('<div class="span2">%(label)s</div>%(field)s &nbsp;&nbsp;days' % {
                'label': bf.label,
                'field': bf
            })
            if name == 'start_time':
                output.append('<div class="slider" id="date_slider"></div>')
        return mark_safe('\n'.join(output))

    def as_custom(self):

        output = []
        for name, field in self.fields.items():
            bf = self[name]
            output.append('<div class="span2">%(label)s</div>%(field)s &nbsp;&nbsp;days' % {
                'label': bf.label,
                'field': bf
            })
        return mark_safe('\n'.join(output))


class EditParasiteForm(CustomModelForm):
    """A class representing the parasite step in the EditWizardView.

    This presents the user with a list of parasite settings
    """
    class Meta:
        """A class to override the default ModelForm Meta

        Sets the model to ConfigData and sets unneeded field widgets to hidden.
        """
        model = ConfigData
        widgets = {
            'name': HiddenInput,
            'description': HiddenInput,
            'type': HiddenInput,
            'misc': HiddenInput,
            'json': JSONConfigWidget}

    def __init__(self, *args, **kwargs):
        """Extension of __init__ method

        Ignore the hidden fields in the form, only get the JSON field
        """
        super(EditParasiteForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            if key in ['name', 'start_day', 'num_repetitions', 'Timesteps_Between_Repetitions']:
                self.fields[key].required = False


class EditScalingForm(CustomForm):
    """ A class representing EditScalingForm """

    x_Temporary_Larval_Habitat = forms.FloatField()
    x_Temporary_Larval_Habitat.widget.attrs['range'] = '0.00, 10000'


class EditSpeciesForm(CustomForm):
    """A class to override the default ModelForm Meta

    Capture the species the user has selected
    """
    species = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())

#: A tuple assigning step names to corresponding Forms
#:
#: Used in EditWizardView
named_edit_forms = (
    ('config', EditConfigForm),
    ('climate', EditClimateForm),
    ('demographic', EditDemographicForm),
    ('species', EditSpeciesForm),
    ('parasite', EditParasiteForm),
    ('scaling_factors', EditScalingForm),
    #('run', EditRunForm),
)
