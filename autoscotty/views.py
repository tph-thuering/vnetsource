import os
import traceback
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView
from autoscotty.forms import UploadZipForm, ReportErrorForm
from autoscotty.tasks import ingest_files
from data_services.file_system_storage import save_to_system
from data_services.ingesters import EMOD_ingester
from data_services.models import DimReplication


class UploadZip(FormView):
    """
    This class handles the main view for the AutoScotty application. It is responsible for accepting and processing
    form submissions. If form submission is successful, an HTTP Response 200 is returned. If the form is invalid, an
    HTTP Response 400 is returned. This class subclasses the Django generic FormView.
    """
    template_name = 'autoscotty/upload.html'
    form_class = UploadZipForm

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        """
        This is the main entry point for the FormView. It is being over-ridden only so the csrf_exempt decorator
        can be applied.
        """
        return super(UploadZip, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """
        This method is called when a form validates successfully. It is responsible for calling the celery ingestion
        task, waiting for a response if synchronous is set to true, and saving the zip files to the system.

        :param autoscotty.forms.UploadZipForm form: The validated form.
        :rtype: - HTTP 200 if successful
                - HTTP 461 if the files could not be saved
        """
        # get the zip files and save them to the file system. We save the file here so that we pass around a path to
        # the file rather than the entire file, which is in memory, not on disk. If the save fails, return an http 461.
        zip_file = form.cleaned_data['zip_file']
        success, message = save_to_system(zip_file)
        if not success:
            return HttpResponse("461: Can't save input file to system", status=461)
        path = message
        print "The files were saved to ", path
        model_type = form.cleaned_data['model_type']
        if 'sync' in form.cleaned_data:
            sync = form.cleaned_data['sync']
        else:
            sync = False
        # ingest the files using Dataingestion apps and celery and save them to the system

        filename = os.path.basename(path)
        ids = filename.split("-")
        if len(ids) == 3:
            # Filename is in format manifest-execid-seriesid.zip
            # For example, manifest-54321-000.zip
            # (\w+)-(\d+)-(\d+).zip
            dummy, execid, seriesid  = ids
            # remove .zip
            seriesid, dummy = seriesid.split(".")
        else:
            # Old EMOD format
            seriesid = None
            execid = None
            #raise TypeError("wrong filename format")

        if not hasattr(settings, "AUTOSCOTTY_DONT_USE_CELERY"):
            try:
                result = ingest_files.delay(path, model_type, execid = execid, seriesid = seriesid)
            except Exception as e:
                stacktrace = traceback.format_exc()
                #traceback.print_exc()
                print stacktrace
                #traceback.print_tb(stacktrace)
                try:
                    send_mail('Ingestion Failure', "An %s ingestion failed. The path is %s\n%s" % (model_type, path, stacktrace),
                        settings.SERVER_EMAIL,
                        [r[1] for r in settings.ADMINS])
                except Exception as e:
                    print "Can't send email: %s" % e
                return HttpResponse("461: Celery failure", status=461)
            if sync is True:
                result.get()    # if synchronous was requested, wait for response
        else:
            # Debug mode for testing new ingestion types on a branch
            #ingest_files(path,model_type, execid = execid, seriesid = seriesid)
            import data_services
            try:
                data_services.ingest.ingest_files(path, model_type, execid = execid, seriesid = seriesid)
            except Exception as e:
                stacktrace = traceback.format_exc()
                #traceback.print_exc()
                print stacktrace
                #traceback.print_tb(stacktrace)
                try:
                    send_mail('Ingestion Failure', "An %s ingestion failed. The path is %s\n%s" % (model_type, path, stacktrace),
                        settings.SERVER_EMAIL,
                        [r[1] for r in settings.ADMINS])
                except Exception as e:
                    print "Can't send email: %s" % e
                return HttpResponse("461: Ingestion failure", status=461)

        return HttpResponse("200: Successfully ingested", status=200)

    def form_invalid(self, form):
        """
        This method is called if the form does not validate successfully.

        :param autoscotty.forms.UploadZipForm form: The invalid form.
        :rtype: - HTTP 400 for general invalid forms.
                - HTTP 460 if the provided hash does not match the computed hash for the zip file.
        """
        status = 400
        if form._errors and 'hash_mismatch' in form._errors:
            status = 460
        return self.render_to_response(self.get_context_data(form=form), status=status)


class ReportError(FormView):
    """
    This class handles the error reporting for AutoScotty. It is responsible for accepting and processing
    errors from the cluster. If form submission is successful, an HTTP Response 200 is returned. If the form is
    invalid, an HTTP Response 400 is returned. If the replication does not exist, an HTTP Response 404 is returned.
    """
    template_name = 'autoscotty/report.html'
    form_class = ReportErrorForm

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        """
        This is the main entry point for the FormView. It is being over-ridden only so the csrf_exempt decorator
        can be applied.
        """
        return super(ReportError, self).dispatch(*args, **kwargs)

    def form_valid(self, form):
        """
        This method is called when a form validates successfully. It is responsible for updating the replication.

        :param autoscotty.forms.ReportErrorForm form: The valid form.
        :rtype: - HTTP 200
        """
        rep = form.cleaned_data['replication']
        message = form.cleaned_data['message']
        status = form.cleaned_data['status']
        execid = form.cleaned_data['execid']
        seriesid = form.cleaned_data['seriesid']
        if execid is not None:
            EMOD_ingester.rep_failed(execid = execid, seriesid = seriesid, msg = message)
        else:
            my_rep = get_object_or_404(DimReplication, pk=rep)
            my_rep.status = status
            my_rep.status_text = message
            my_rep.save()

        return HttpResponse("200: OK", status=200)

    def form_invalid(self, form):
        """
        This method is called if the form does not validate successfully.

        :param autoscotty.forms.ReportErrorForm form: The invalid form.
        :rtype: - HTTP 400
        """
        status = 400
        return self.render_to_response(self.get_context_data(form=form), status=status)