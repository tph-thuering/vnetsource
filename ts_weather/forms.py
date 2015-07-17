from django.forms import ModelForm
from django import forms
from .models import CsvFileUpload, ClimateFilesUpload

class CsvUploadForm(ModelForm):
    class Meta:
        model = CsvFileUpload

class ClimateUploadForm(ModelForm):
    class Meta:
        model = ClimateFilesUpload

class CsvDownloadForm(forms.Form):
    filePrefix = forms.CharField(max_length=100, label='File Name')

class EmodDownloadForm(forms.Form):
    filePrefix = forms.CharField(max_length=100, label='File Name')
    idReference = forms.CharField(max_length=100, label='Id Reference')
    updateResolution = forms.CharField(max_length=100, label='Update Resolution')
    dataProvenance = forms.CharField(max_length=100, label='Data Provenance')
