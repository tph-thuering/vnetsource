########################################################################################################################
# VECNet CI - Prototype
# Date: 03/07/2014
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

from ts_emod.forms import CustomForm, CustomModelForm
from ts_emod.models import ConfigData
from ts_emod.fields import UnValidatedMultipleChoiceField, JSONConfigWidget


class BaselineLocationForm(CustomForm):
    """A class representing the location feedback step in the BaselineWizardView.

    This displays graphs of the user-selected location data for the user to review.
    """
    template_id = forms.IntegerField()


class BaselineRunForm(CustomForm):
    """A class representing the run step in the BaselineWizardView.

    This is currently the intended entry point to the BaselineWizard
    though wizards allow step to be taken out of order.
    """
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Type in a short name for the test run',
                                                         'required': ''}))


class BaselineClimateForm(CustomForm):
    """A class representing the location step in the BaselineWizardView.

    This presents the user with a list of locations pulled from the EMOD_Adapter (Datawarehouse/Digital Library).
    This list represents the available data sets to be used in simulations.
    """
    #location = forms.ModelChoiceField(queryset=Location.objects.order_by('name').filter(is_public=1),
    # empty_label="Please select a location")
    #adapter = EMOD_Adapter()
    #try:
    #    location_dict = adapter.fetch_locations()
    #    CHOICES = [("", "Please select a data set")]
    #    CHOICES.append((242, 'Binh Long, Vietnam: 1995 - 2004'))
    #    for x in location_dict.keys():
    #        location_dict[x].update({'id': x})
    #
    #    CHOICES = CHOICES + [(x,
    #                         location_dict[x]['place'] + ', ' +
    #                         location_dict[x]['country'] + ': ' +
    #                         location_dict[x]['start_date'].split('-')[0] + ' - ' +
    #                         location_dict[x]['end_date'].split('-')[0])
    #                         for x in location_dict.keys()]
    #except KeyError:
    #    CHOICES = []

    #location_list = adapter.fetch_locations()
    #CHOICES = [("", "Please select a location")]
    #CHOICES = CHOICES + [(x,
    #            x['place'] + ', ' +
    #            x['country'] + ': ' +
    #            x['start_date'].split('-')[0] + ' - ' +
    #            x['end_date'].split('-')[0])
    #           for x in location_list]

    #location = forms.ChoiceField(label="", choices=CHOICES, widget=forms.Select(attrs={'style': "width: 260px;"}))


class BaselineDemographicForm(CustomForm):
    """A class representing the location feedback step in the BaselineWizardView.

    This displays graphs of the user-selected location data for the user to review.
    """
    class Meta:
        widgets = {'placeholder': HiddenInput}


class BaselineConfigForm(CustomForm):
    """A class representing the config step in the BaselineWizardView.

    This allows the user to specify the date-range of location data to use in the simulation.
    Range is specified by location data in Location DB table.
    """
    name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Type in a short name for the simulation',
                                                         'required': ''}))
    description = forms.CharField(help_text=mark_safe('<span class="helptext-narrow">Characters '
                                                      'remaining: <span id="count"></span></span>'),
                                  widget=forms.Textarea(attrs={'class': 'description-box',
                                  'placeholder': 'Type in a short description of the simulation'}))

    #: Specify the start and end of the date range
    Start_Time = forms.IntegerField(widget=forms.TextInput(attrs={'style': "width: 60px"}))
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
        super(BaselineConfigForm, self).__init__(*args, **kwargs)
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


class BaselineInterventionForm(CustomForm):
    """A class representing the Intervention selection step in the BaselineWizardView.

    This displays the interventions (from Intervention DB table) and
    allows the user to select zero or more from the list.
    Interventions can be selected more than once.
    Users can specify a number of fields to associate to the selected Intervention instance.

    - Using UnValidatedMultipleChoiceField so that an array of values of each type is captured by the form
    - all interventions on one array, start_days in another.  Indexed in proper order.
    """
    interventions = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())
    start_day = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())
    num_repetitions = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())
    Timesteps_Between_Repetitions = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())
    Number_Distributions = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())
    demographic_coverage = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())

    def __init__(self, *args, **kwargs):
        """Extension of __init__ method

        Allow zero interventions to be selected
        What about validating fields in interventions that are selected?
        """
        super(BaselineInterventionForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            if key in ['intervention_list', 'start_day', 'num_repetitions', 'Timesteps_Between_Repetitions',
                       'Number_Distributions']:
                self.fields[key].required = False

    def clean(self):
        """ Custom clean method: Converts demographic_coverage from percent back to decimal
        (js/form makes it a percent) """

        cleaned_data = super(BaselineInterventionForm, self).clean()
        try:
            for i in range(len(dict(self.data)['intervention-demographic_coverage'])):
                #if float(dict(self.data)['intervention-demographic_coverage'][i]) > 1.0:
                # this ended up be considered a bug - we thought users would never mean to use less than 1%. Ben does.
                dict(self.data)['intervention-demographic_coverage'][i] =\
                    float(dict(self.data)['intervention-demographic_coverage'][i]) / 100
        except:
            pass
        return cleaned_data


class BaselineParasiteForm(CustomModelForm):
    """A class representing the parasite step in the BaselineWizardView.

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
        super(BaselineParasiteForm, self).__init__(*args, **kwargs)
        for key in self.fields:
            if key in ['name', 'start_day', 'num_repetitions', 'Timesteps_Between_Repetitions']:
                self.fields[key].required = False


class BaselineScalingForm(CustomForm):
    """ A class representing BaselineScalingForm """

    x_Temporary_Larval_Habitat = forms.FloatField()
    x_Temporary_Larval_Habitat.widget.attrs['range'] = '0.00, 10000'


class BaselineCalibrationForm(CustomForm):
    """ A class representing BaselineScalingForm """
    class Meta:
        """A class to override the default ModelForm Meta

        Sets the model to ConfigData and sets unneeded field widgets to hidden.
        """

    #name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Type in a short name for the scenario',
    #                                                     'required': ''}))


class BaselineReviewForm(CustomForm):
    """A class representing the preview step in the BaselineWizardView.

    This displays all the data collected in the previous steps.
    Also displays any missing data.
    This allows the user to submit the collected data to processing
    If the user attempts to submit to processing with missing required data
    the user is redirected to the step to populate that data.
    """
    class Meta:
        widgets = {'placeholder': HiddenInput}


#class BaselineSpeciesForm(CustomForm):
#    #class Meta:
#    #    widgets = {'placeholder': HiddenInput}
#    species = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())

#class SpeciesCreateForm(CustomModelForm):
class BaselineSpeciesForm(CustomForm):
    """A class to override the default ModelForm Meta

    Capture the species the user has selected
    """
    species = UnValidatedMultipleChoiceField(widget=forms.MultipleHiddenInput())

#: A tuple assigning step names to corresponding Forms
#:
#: Used in BaselineWizardView
named_baseline_forms = (
    ('location', BaselineLocationForm),
    ('config', BaselineConfigForm),
    ('climate', BaselineClimateForm),
    ('demographic', BaselineDemographicForm),
    ('species', BaselineSpeciesForm),
    ('parasite', BaselineParasiteForm),
    ('scaling_factors', BaselineScalingForm),
    # ('calibration', BaselineCalibrationForm),
    ('run', BaselineRunForm),
    ('review', BaselineReviewForm),
)
