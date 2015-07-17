from django import forms

class dlform(forms.Form):
    # TODO Add class docstring
    file_name = forms.CharField(max_length = 50)
    content = forms.CharField(widget=forms.HiddenInput())
