"""
Contains the base class for autoscotty EMOD functional tests.
"""
import requests
import datetime
import os
import hashlib
import time

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from optparse import make_option

from data_services.models import DimRun, DimUser, DimModel, DimTemplate, DimLocation, \
    DimExecution, DimReplication
from data_services.adapters.EMOD import EMOD_Adapter
from django.contrib.auth.models import User


class EMODTestBase(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--template',
                    action='store',
                    type="int",
                    dest='template',
                    default=False,
                    help='The template to associate to the scenario.'),
        make_option('--ingestURL',
                    action='store',
                    type="string",
                    dest='ingestURL',
                    default=False,
                    help='The ingestion URL.'),
    )

    def handle(self, *args, **options):
        """
        Main function for command.
        """
        # setup some configuration for the test
        self.newfilename = None
        self.eir_channel = 228441
        self.run = None
        # run each step using functions
        try:
            self.verify_and_store_command_line_options(options)
            self.create_model_input_structure()
            self.launch_job()
            self.get_replication_and_execution()
            self.verify_ingested_data()
            self.remove_data()
            self.notify_admins_of_success("The functional test for autoscotty and EMOD was successfully ran on %s" %
                                          str(datetime.datetime.now()))
        except Exception as e:
            self.notify_admins_of_error(e)

    def verify_and_store_command_line_options(self, options):
        """
        Checks that the command line options are valid.
        """
        # get template
        template_id = options.get('template', None)
        if template_id != 0 and not template_id:
            raise ValueError("You must specify a template id.")
        try:
            self.template = DimTemplate.objects.get(id=template_id)
        except DimTemplate.DoesNotExist as e:
            raise e

        # get url
        self.urlname = options.get('ingestURL', None)
        if not self.urlname:
            ingestion_urls = getattr(settings, "AUTOSCOTTY_INGESTION_URLS", None)
            if not ingestion_urls:
                message = "You must pass in an ingestion url at the command line, or define AUTOSCOTTY_INGESTION_URLS" \
                          " in your settings.py file."
                raise Exception(message)
            app_env = getattr(settings, "APP_ENV", None)
            if app_env:
                self.urlname = ingestion_urls[app_env]
            else:
                self.urlname = ingestion_urls["default"]

    def create_model_input_structure(self):
        """
        Creates a run for the test.
        """
        try:
            self.dim_user, created = DimUser.objects.get_or_create(username="autoscottyEmodTest")
            self.user, created = User.objects.get_or_create(username="autoscottyEmodTest")
            self.adaptor = EMOD_Adapter(self.dim_user.username)
            self.start_date = datetime.datetime.now()
            self.end_date = datetime.datetime.now() + datetime.timedelta(789)
            self.model = DimModel.objects.get(model="EMOD")
            self.location, created = DimLocation.objects.get_or_create(geom_key=12345)
            self.template = DimTemplate.objects.get(id=self.template.id)
            self.run = DimRun.objects.create(start_date_key=self.start_date,
                                             end_date_key=self.end_date,
                                             location_key=self.location,
                                             template_key=self.template,
                                             models_key=self.model,
                                             name="autoscotty_emod_test_run",
                                             description="just a test",
                                             timestep_interval_days=1)
            self.adaptor.add_channels(self.run.id)
        except Exception as e:
            message = "An error occured creating the input structures. Below are the exception details: \n" + str(e)
            raise Exception(message)

    def launch_job(self):
        """
        Since different ingestion types (manifest, non-manifest) use different launching mechanisms, this method
        must be specified by a class inheriting from this base class.
        """
        raise Exception("Implement this method based on your ingestion type(manifest or non-manifest).")

    def get_replication_and_execution(self):
        """
        After launching the job, this function retrieves and stores the created replication and execution.
        """
        try:
            self.execution = DimExecution.objects.get(run_key=self.run)
            self.replication = DimReplication.objects.get(execution_key=self.execution)
        except Exception as e:
            raise e

    def create_ingest_file(self):
        """
        Since different ingestion types (manifest, non-manifest) use different naming conventions, this method
        must be specified by a class inheriting from this base class.
        """
        raise Exception("Implement this method based on your file type(manifest or non-manifest).")

    def ingest_output(self):
        """
        Ingest the output data using autoscotty.
        """
        try:
            self.create_ingest_file()
            # Curl the files to AutoScotty
            f = open(self.newfilename, 'rb')
            files = {'zip_file': f}
            myhash = hashlib.sha1()
            myhash.update(f.read())
            f.seek(0)
            r = requests.post(self.urlname,
                              files=files,
                              data={'model_type': "EMOD", 'sync': False, 'zip_file_hash': myhash.hexdigest()})
            if r.status_code != 200:
                message = "There was an ingestion error at the server. The HTTP Response code is: ", r.status_code
                raise Exception(message)
        except Exception as e:
            raise e

    def verify_ingested_data(self):
        """
        Verify that the correct data was ingested into the database.
        """
        result_dict = self.adaptor.fetch_data(run_id=self.run.id,
                                              channel_name="Daily EIR",
                                              execution_id=self.execution.id,
                                              group_by=True)
        results = result_dict[self.run.name + " 1"]
        # if results do not appear within 15 minutes, notify admins and exit
        timeout = time.time() + 60 * 15   # 15 minutes from now
        while len(results) == 0:
            if time.time() > timeout:
                break
            time.sleep(10)
            result_dict = self.adaptor.fetch_data(run_id=self.run.id,
                                                  channel_name="Daily EIR",
                                                  execution_id=self.execution.id,
                                                  group_by=True)
            results = result_dict[self.run.name + " 1"]

        if len(results) == 0:
            message = "The data was not ingested within 15 minutes. Run: %i" % self.run.id
            raise Exception(message)

        # Compare yearly-aggregated data in channel "Daily EIR" with expected result.
        year1_sum = results[0]
        year2_sum = results[1]
        if round(year1_sum, 0) != 193 or round(year2_sum, 0) != 288:
            message = "The ingested data has an unexpected aggregate value.\nExpected: year1 193.087, year2 287.634 \n"
            message += "Actual: year1 %s, year2 %s" % (str(year1_sum), str(year2_sum))
            raise Exception(message)

    def remove_data(self):
        """
        Remove the ingested data and the temporary file.
        """
        # "Soft" delete run.
        try:
            self.adaptor.delete_run(self.run.id)
        except Exception as e:
            raise e
        # remove temporary file
        try:
            os.remove(self.newfilename)
        except Exception as e:
            raise e

    def notify_admins_of_error(self, message):
        """
        Notifies admins of the error that occurs.
        """
        new_message = ""
        new_message = "While running a functional test for EMOD data ingestion, an error occured.\n"
        new_message += "Here is the message and/or traceback: \n"
        new_message += "\nRun: %s \n" % self.run.id
        new_message += str(message)
        print new_message
        exit()

    def notify_admins_of_success(self, message):
        """
        Send the admins a success message.
        """
        print str(message) + "\nRun: %s \n" % self.run.id
        exit()