import json
import os
import time
import shutil
from data_services.models import DimExecution

from change_doc import JCD
from job_services import dispatcher
from .emod_test_base import EMODTestBase


## Manifest Version
class Command(EMODTestBase):
    """
    Management command to test launching and ingestion of an EMOD job that uses manifest.
    """
    def handle(self, *args, **options):
        """
        Main entry point for Command.
        """
        super(Command, self).handle(*args, **options)

    def create_model_input_structure(self):
        """
        Creates a run for the test.
        """
        super(Command, self).create_model_input_structure()
        try:
            # changes = open(os.path.join(os.path.dirname(__file__), 'changes.json'))
            # data = json.load(changes)
            # changes.close()
            self.run.jcd = JCD()
            self.run.save()
        except Exception as e:
            raise e

    def launch_job(self):
        """
        Submit the job to the cluster for processing.
        """
        try:
            dispatcher.submit(self.run, self.user, reps_per_exec=1, manifest=True)
        except Exception as e:
            raise e

    def get_replication_and_execution(self):
        """
        After launching the job, this function retrieves and stores the created execution.
        """
        try:
            self.execution = DimExecution.objects.get(run_key=self.run)
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
        results = result_dict[self.run.name]
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
            results = result_dict[self.run.name]

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