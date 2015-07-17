import mock

from django.test import TestCase

from lib.error_mixins import CallerErrorMixin

from job_services.tests.mocks.data_services_mocks import mock_num_jobs
from ..dispatcher import submit
from .. import cluster_id, dispatcher
from ..api import ApiErrors
from ..models import SubmittedJobs, RunProvider
from ..providers import provider_name
from .data_mixins import SetupRunMixin
from .mocks.mixins import MockProviderMixin


MOCK_CLUSTER = cluster_id.TestingApi.MOCK_ID
MOCK_PROVIDER = provider_name.TestingApi.MOCK_NAME
MOCK_FALSE_MESSAGE = "Mock false message"


class DispatcherTests(SetupRunMixin, MockProviderMixin, CallerErrorMixin, TestCase):
    """
    Base class for unit tests for the dispatcher.
    """
    @classmethod
    def setUpClass(cls):
        cls.bad_run_id = 9999

    def setUp(self):
        """
        Create a run for use in the tests.
        """
        self.setup_run()
        self.enable_mock_provider()

    def tearDown(self):
        self.disable_mock_provider()


class StatusQueryTests(DispatcherTests):
    """
    Unit tests for the get_status function in the dispatcher's API.
    """
    def test_get_status_with_wrong_run_type(self):
        self.assertCallerError(ApiErrors.RUN_PARAM_BAD_TYPE, dispatcher.get_status, None, self.user)

    def test_get_status_with_bad_run_id(self):
        self.assertCallerError(ApiErrors.RUN_PARAM_BAD_ID, dispatcher.get_status, self.bad_run_id, self.user)

    def test_get_status_with_wrong_user_type(self):
        self.assertCallerError(ApiErrors.USER_PARAM_BAD_TYPE, dispatcher.get_status, self.run, None)

    def test_get_status_for_unsubmitted_run(self):
        self.assertCallerError(ApiErrors.RUN_NOT_SUBMITTED, dispatcher.get_status, self.run, self.user)

    @mock.patch('job_services.dispatcher.logging')
    def test_get_status_with_no_provider_returned(self, mock_logging):
        mock_logger = mock.Mock()
        attrs = {'getLogger.return_value': mock_logger}
        mock_logging.configure_mock(**attrs)
        RunProvider.objects.create(run=self.run, provider="mock_return_none")
        self.assertRaises(AssertionError, dispatcher.get_status, self.run, self.user)

        #  Check if the logger's "exception" method was called
        self.assertEqual(len(mock_logger.method_calls), 1)
        first_call = mock_logger.method_calls[0]
        self.assertEqual(first_call[0], 'exception')

    @mock.patch("job_services.dispatcher.has_been_submitted")
    def test_get_status(self, mock_has_been_submitted):
        """
        Tests for the get_status function.
        """
        # Associate the mock provider with the existing model run
        RunProvider.objects.create(run=self.run, provider=MOCK_PROVIDER)
        mock_has_been_submitted.return_value = True

        # test with a run object
        status = dispatcher.get_status(self.run, self.user)
        self.assertEqual(status.n_replications, 100)
        self.assertEqual(status.completed_replications, 50)
        self.assertEqual(status.failed_replications, 10)

        # test with a run id
        status = dispatcher.get_status(self.run.id, self.user)
        self.assertEqual(status.n_replications, 100)
        self.assertEqual(status.completed_replications, 50)
        self.assertEqual(status.failed_replications, 10)


class SubmissionTests(DispatcherTests):
    """
    Unit tests for the submit function in the dispatcher's API.
    """

    def test_submit_with_wrong_run_type(self):
        self.assertCallerError(ApiErrors.RUN_PARAM_BAD_TYPE, submit, "foo", self.user)

    def test_submit_with_bad_run_id(self):
        self.assertCallerError(ApiErrors.RUN_PARAM_BAD_ID, submit, self.bad_run_id, self.user)

    def test_submit_with_wrong_user_type(self):
        self.assertCallerError(ApiErrors.USER_PARAM_BAD_TYPE, submit, self.run, self.dim_user)

    @mock.patch("job_services.dispatcher.has_been_submitted")
    def test_submit_with_already_submitted_run(self, mock_has_been_submitted):
        mock_has_been_submitted.return_value = True
        self.assertCallerError(ApiErrors.RUN_ALREADY_SUBMITTED, dispatcher.submit, self.run, self.user)

    def test_submit_with_wrong_cluster_type(self):
        """
        Test the submit function with a cluster parameter of the wrong type.
        """
        self.assertCallerError(ApiErrors.CLUSTER_PARAM_BAD_TYPE, submit, self.run, self.user, cluster=3.14)
        self.assertCallerError(ApiErrors.CLUSTER_PARAM_BAD_TYPE, submit, self.run, self.user, cluster=None)
        self.assertCallerError(ApiErrors.CLUSTER_PARAM_BAD_TYPE, submit, self.run, self.user, cluster=dict())

    def test_submit_with_invalid_cluster(self):
        """
        Test the submit function with an invalid cluster id.
        """
        # run id and non valid cluster
        self.assertCallerError(ApiErrors.CLUSTER_PARAM_BAD_ID, submit, self.run.id, self.user, cluster="INVALID")
        # run object and non valid cluster
        self.assertCallerError(ApiErrors.CLUSTER_PARAM_BAD_ID, submit, self.run, self.user, cluster="INVALID")

    @mock.patch("job_services.dispatcher._selection_algorithm")
    def test_submit_with_no_provider_returned(self, mock_algorithm):
        mock_algorithm.return_value = None, MOCK_FALSE_MESSAGE
        message_regex = "^%s$" % MOCK_FALSE_MESSAGE  # Fragile -- assumes no regex characters in message
        self.assertRaisesRegexp(RuntimeError, message_regex,
                                submit, self.run.id, self.user, reps_per_exec=True, cluster=MOCK_CLUSTER, manifest=True)

    @mock.patch("data_services.models.DimRun.numjobs", mock_num_jobs.mock_num_jobs)
    def test_submit_with_success(self):
        """
        Test the submit function with successful submission.
        """
        #TODO test dates that are commented out below
        # run id and valid cluster and successful submission
        submit(self.run.id, self.user, reps_per_exec=True, cluster=MOCK_CLUSTER, manifest=True)
        obj = SubmittedJobs.objects.all()[0]
        first_SubmittedJobs_obj = obj
        self.assertEqual(obj.user, self.user)
        self.assertEqual(obj.cluster, MOCK_CLUSTER)
        self.assertEqual(obj.number_of_jobs, 100)
        #self.assertEqual(obj.date, datetime.date.today())
        obj = RunProvider.objects.get(run=self.run)
        self.assertEqual(obj.run, self.run)
        self.assertEqual(obj.provider, MOCK_PROVIDER)

        # run object and valid cluster and successful submission
        RunProvider.objects.all().delete()
        submit(self.run, self.user, reps_per_exec=True, cluster=MOCK_CLUSTER, manifest=True)
        obj = SubmittedJobs.objects.exclude(pk=first_SubmittedJobs_obj.id)[0]
        self.assertEqual(obj.user, self.user)
        self.assertEqual(obj.cluster, MOCK_CLUSTER)
        self.assertEqual(obj.number_of_jobs, 100)
        #self.assertEqual(obj.date, datetime.date.today())
        obj = RunProvider.objects.get(run=self.run)
        self.assertEqual(obj.run, self.run)
        self.assertEqual(obj.provider, MOCK_PROVIDER)

    @mock.patch("data_services.models.DimRun.numjobs", mock_num_jobs.mock_num_jobs)
    def test_submit_without_success(self):
        """
        Test the submit function with failed submission.
        """
        # run id and valid cluster and Unsuccessful submission
        self.assertRaises(RuntimeError, submit, self.run.id, self.user, reps_per_exec=False, cluster=MOCK_CLUSTER)

        # run object and valid cluster and Unsuccessful submission
        self.assertRaises(RuntimeError, submit, self.run, self.user, reps_per_exec=False, cluster=MOCK_CLUSTER)


class ConfigureComponentTests(TestCase):
    """
    Tests that the configure component function is called when dispatcher is loaded.
    """
    @mock.patch("job_services.conf.configure_component")
    def test_configure_component(self, mock_configure_component):
        reload(dispatcher)
        self.assertTrue(mock_configure_component.called)