"""
Mixin classes for creating test data.
"""
from change_doc import JCD
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from data_services.models import DimLocation, DimModel, DimRun, DimTemplate, DimUser, DimReplication, DimExecution
from data_services import emod_id

from .. import util
from change_doc import JCD


class SetupRunMixin(object):
    """
    Mixin for test suites that need a DimRun object.
    """
    def setup_run(self):
        """
        Setup a DimRun object with the minimal set of dependent objects.
        """
        self.user = User.objects.create_user(username="foobar", password='1')
        self.dim_user = DimUser.objects.create(username="foobar")
        self.date = timezone.datetime.now(timezone.utc)
        self.model = DimModel.objects.create(id=1, model="test_model")
        self.OM_model = DimModel.objects.create(id=util.OPEN_MALARIA_ID, model="OM_test_model")
        self.location = DimLocation.objects.create(geom_key=12345)
        self.template = DimTemplate.objects.create(model_key=self.model,
                                                   user=self.dim_user)
        self.run = DimRun.objects.create(
                                         start_date_key=self.date,
                                         end_date_key=self.date,
                                         location_key=self.location,
                                         template_key=self.template,
                                         models_key=self.model,
                                         name="job_services_test_run",
                                         description="just a test",
                                         timestep_interval_days=789,
                                         model_version = emod_id.EMOD15)

    def add_executions_and_replications(self, number_to_add):
        """
        Create executions for the run setup above. This method assumes a "self.run" object exists and is a DimRun.
        One replication is added per execution. Half of the replications are created with a failed status, and half
        are created with a completed status. If an odd number of executions are created, the off replication will have
        a completed status.
        :param int number_to_add: The number of executions to add.
        """
        COMPLETED_STATUS = 0
        FAILED_STATUS = 1
        for i in range(0, number_to_add):
            if i % 2 == 1:
                status = COMPLETED_STATUS
            else:
                status = FAILED_STATUS
            execution_name = "Test execution %i" % i
            execution = DimExecution.objects.create(run_key=self.run, name=execution_name, replications=1, jcd=JCD())
            DimReplication.objects.create(seed_used=9999,
                                          series_id=9999,
                                          execution_key=execution,
                                          status=status,
                                          status_text="Test replication status.")

    def add_executions(self, number_to_add):
        """
        Create executions for the run setup above. This method assumes a "self.run" object exists and is a DimRun.
        One replication is added per execution.
        :param int number_to_add: The number of executions to add.
        """
        for i in range(0, number_to_add):
            execution_name = "Test execution %i" % i
            execution = DimExecution.objects.create(run_key=self.run, name=execution_name, replications=1, jcd=JCD())
            DimReplication.objects.create(seed_used=9999,
                                          series_id=9999,
                                          execution_key=execution,
                                          status=0,
                                          status_text="Test replication status.")