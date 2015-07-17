import hashlib
from django import forms
from data_services.models import DimModel

__author__ = 'Alexander'


class UploadZipForm(forms.Form):
    """
    This class defines the form used to upload files.

    :param FileField zip_file: The zip file to ingest.
    :param BooleanField sync: A boolean flag indicating whether or not the user wishes to perform a synchronous
     celery task.
    :param CharField zip_file_hash: A hash of the zip file. This is used to verify the integrity of the
     submitted zip file.
    :param string model_type: A string indicating what simulation model produced the data.
    """
    # TODO Add attribute docstring(s)
    zip_file = forms.FileField()
    sync = forms.BooleanField(initial=False, required=False)
    zip_file_hash = forms.CharField(required=False)
    model_type = forms.ChoiceField()
    #model_type = forms.CharField(required=False)
    execid = forms.IntegerField(required=False)
    seriesid = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        """
        Get the choices at object creation time instead of class definition time.
        """
        super(UploadZipForm, self).__init__(*args, **kwargs)
        self.fields['model_type'].choices = ((model.model, model.model) for model in DimModel.objects.all())

    def clean(self):
        """
        This is a custom clean method for the zip_file_hash variable. It checks that the provided hash string matches
        the hash of the submitted file.  If there's a difference, then the zip_file likely lost data during
        transmission, and should be resubmitted.

        :raises: ValidationError
        :returns: The cleaned_data dictionary of the form.
        """
        cleaned_data = super(UploadZipForm, self).clean()
        # get the file, create a hash of it, and compare it to the provided hash. If they do not match, raise an error.
        f = cleaned_data.get('zip_file')
        h = cleaned_data.get('zip_file_hash')

        if f and h:
            myhash = hashlib.sha1()
            if f.multiple_chunks():
                for chunk in f.chunks():
                    myhash.update(chunk)
            else:
                myhash.update(f.read())
            if str(myhash.hexdigest()) != str(h) and (h != "na"):
                self._errors["hash_mismatch"] = self.error_class(["The hash does not match the file."])

        return cleaned_data

    def clean_model_type(self):
        """
        This is a custom clean method for the model_type field of the form. If the model_type field is not specified,
        it is given a default".
        """
        m = self.cleaned_data['model_type']
        if m is None:
            return "UNSPECIFIED"
        return m


class ReportErrorForm(forms.Form):
    """
    This class defines the form used to report a failed job on the cluster.

    :param IntegerField replication: The replication number corresponding to a replication in the database.
    :param IntegerField status: An integer representing the status of the replication.
    :param CharField message: A message detailing the status of the replication.

    """
    # TODO Add attribute docstring(s)
    replication = forms.IntegerField(required=False)
    execid = forms.IntegerField(required=False)
    seriesid = forms.IntegerField(required=False)
    status = forms.IntegerField()
    message = forms.CharField(widget=forms.Textarea)