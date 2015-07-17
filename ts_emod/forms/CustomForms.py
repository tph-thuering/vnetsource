########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################

# Imports that are external to the ts_emod app

from django import forms
from django.forms import HiddenInput, ModelForm
from django.utils.safestring import mark_safe
from data_services.models import DimNotes


class CustomForm(forms.Form):
    """Extension of forms.Form to allow for reuse of common customizations

    - define " " as label_suffix instead of ":"
    - make as_grid_div is available in all
    """
    def __init__(self, *args, **kwargs):
        """Override init to define " " as label_suffix instead of ":"
        """
        kwargs.setdefault('label_suffix', '')
        super(CustomForm, self).__init__(*args, **kwargs)

    def as_grid_div(self):
        """Extension of the form to provide an alternative formatting in Template.

        Returns this form rendered as HTML::

            <div class=span1/1>s -- excluding the <div class=row></div>."

        in case you are adding to existing row
        """
        return self._html_output(
            normal_row='<div class="span1">%(label)s</div><div class="span1">%(field)s%(help_text)s</div></div>'
                       '<div class="row"><div class="span1"></div><div class="span2">%(errors)s</div></div> '
                       '<div class="row">',
            error_row='%s',
            row_ender='</div>',
            help_text_html='<span class="helptext">%s</span>',
            errors_on_separate_row=False)

    def as_grid_div_wide(self):
        """Extension of the form to provide an alternative formatting in Template.

        Returns this form rendered as HTML::

            <div class=span2/1>s -- excluding the <div class=row></div>."

        in case you are adding to existing row
        """
        return self._html_output(
            normal_row='<div class="span2">%(label)s</div><div class="span1">%(field)s%(help_text)s</div></div>'
                       '<div class="row"><div class="span1"></div><div class="span2">%(errors)s</div></div> '
                       '<div class="row">',
            error_row='%s',
            row_ender='</div>',
            help_text_html='<span class="helptext">%s</span>',
            errors_on_separate_row=False)


class CustomModelForm(ModelForm):
    """Extension of ModelForm to allow for reuse of common customizations

    - define " " as label_suffix instead of ":"
    - make as_grid_div is available in all
    """
    def __init__(self, *args, **kwargs):
        """Override init to define " " as label_suffix instead of ":"
        """
        kwargs.setdefault('label_suffix', '')
        super(CustomModelForm, self).__init__(*args, **kwargs)

    def as_grid_div(self):
        """Extension of the form to provide an alternative formatting in Template.

        Returns this form rendered as HTML::

            <div class=span1/1>s -- excluding the <div class=row></div>."
        """
        return self._html_output(
            normal_row='<div class="span1">%(label)s</div><div class="span1">%(field)s%(help_text)s</div></div>'
                       '<div class="row"><div class="span1"></div><div class="span2">%(errors)s</div></div> '
                       '<div class="row">',
            error_row='%s',
            row_ender='</div>',
            help_text_html='<span class="helptext">%s</span>',
            errors_on_separate_row=False)


class NoteCreateForm(CustomModelForm):
    # TODO Add class docstring
    class Meta:
        model = DimNotes
        exclude = ['run_key']
        widgets = {'text': forms.Textarea(attrs={'class': 'description-box', 'label': '',
                                                 'placeholder': 'Type in a note for this run and click save.',
                                                 'required': ''})}
