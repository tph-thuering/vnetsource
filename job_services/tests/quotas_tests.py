import mock
from django.test import TestCase
from django.utils import timezone
from job_services.tests.mocks.data_services_mocks import mock_num_jobs
from .conf_err_mixins import ConfigurationErrorMixin
from .data_mixins import SetupRunMixin
from ..models import Quota, SubmittedJobs
from ..quotas import exceeds_quota, submitted_this_month, ConfigurationErrorCodes
from .. import quotas, conf_err


class QuotasTests(SetupRunMixin, TestCase):
    """
    Unit tests for the quotas file.
    """
    def setUp(self):
        """
        Setup a run and user.
        """
        self.cluster = "Mock"
        self.setup_run()

    @mock.patch('job_services.tests.data_mixins.DimRun.numjobs', mock_num_jobs.mock_num_jobs)
    def test_exceeds_quota(self):
        """
        Tests for the exceeds quota function.
        """
        ###################################### test default quota ######################################################
        # set the defaults
        quotas._max_per_run = 10
        quotas._max_per_month = 10
        # test exceeds run
        self.assertEqual(exceeds_quota(self.run, self.user, self.cluster), (True, quotas.EXCEEDS_RUN_QUOTA))
        # test exceeds month
        quotas._max_per_run = 100
        self.assertEqual(exceeds_quota(self.run, self.user, self.cluster), (True, quotas.EXCEEDS_MONTHLY_QUOTA))
        # test exceeds month
        SubmittedJobs.objects.create(user=self.user,
                                     cluster=self.cluster,
                                     date=timezone.datetime.now(timezone.utc),
                                     number_of_jobs=100)
        quotas._max_per_month = 199
        self.assertEqual(exceeds_quota(self.run, self.user, self.cluster), (True, quotas.EXCEEDS_MONTHLY_QUOTA))
        # test passes
        quotas._max_per_month = 200
        self.assertEqual(exceeds_quota(self.run, self.user, self.cluster), (False, quotas.QUOTA_NOT_EXCEEDED))

        #################################### test user who has a quota #################################################
        quota = Quota.objects.create(user=self.user, cluster=self.cluster, max_per_run=99, max_per_month=100)
        # test exceeds run
        self.assertEqual(exceeds_quota(self.run, self.user, self.cluster), (True, quotas.EXCEEDS_RUN_QUOTA))
        # test exceeds month
        quota.max_per_run = 100
        quota.save()
        self.assertEqual(exceeds_quota(self.run, self.user, self.cluster), (True, quotas.EXCEEDS_MONTHLY_QUOTA))
        # test passes
        quota.max_per_month = 200
        quota.save()
        self.assertEqual(exceeds_quota(self.run, self.user, self.cluster), (False, quotas.QUOTA_NOT_EXCEEDED))

    def test_submitted_this_month(self):
        """
        Tests the submitted_this_month function.
        """
        today = timezone.datetime.now(timezone.utc).date()
        self.assertEqual(submitted_this_month(self.user, self.cluster, today.month), 0)
        SubmittedJobs.objects.create(user=self.user,
                                     cluster=self.cluster,
                                     date=today,
                                     number_of_jobs=100)
        self.assertEqual(submitted_this_month(self.user, self.cluster, today.month), 100)
        SubmittedJobs.objects.create(user=self.user,
                                     cluster=self.cluster,
                                     date=today,
                                     number_of_jobs=100)
        self.assertEqual(submitted_this_month(self.user, self.cluster, today.month), 200)


class QuotaConfigTests(ConfigurationErrorMixin, TestCase):
    """
    Unit tests for the quotas file.
    """

    def test_load_defaults_with_wrong_type(self):
        """
        Test the load_defaults function with a parameter of the wrong data type (not a dictionary).
        """
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, quotas.load_defaults, None)
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, quotas.load_defaults, -8)
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, quotas.load_defaults, tuple())
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, quotas.load_defaults, [1, 2, 3])
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, quotas.load_defaults, "foo")

    def test_load_defaults_with_no_keys(self):
        """
        Test the load_defaults function with no keys.
        """
        settings_dict = {}
        self.assertRaisesConfError(ConfigurationErrorCodes.MAX_PER_MONTH_EXISTS, quotas.load_defaults, settings_dict)
        settings_dict['max per month'] = 10
        self.assertRaisesConfError(ConfigurationErrorCodes.MAX_PER_RUN_EXISTS, quotas.load_defaults, settings_dict)

    def test_load_defaults_with_non_integer_keys(self):
        """
        Test the load_defaults function with non-integer keys.
        """
        settings_dict = {'max per month': 'hi', 'max per run': 'bye'}
        self.assertRaisesConfError(ConfigurationErrorCodes.MAX_PER_MONTH_TYPE, quotas.load_defaults, settings_dict)
        settings_dict['max per month'] = 10
        self.assertRaisesConfError(ConfigurationErrorCodes.MAX_PER_RUN_TYPE, quotas.load_defaults, settings_dict)