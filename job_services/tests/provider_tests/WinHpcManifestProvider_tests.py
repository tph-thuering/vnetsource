import mock
import data_services
from django.test import TestCase
from django.test.utils import override_settings
from ..data_mixins import SetupRunMixin
from ... import clusters
from ...providers import provider_name
from ...providers.definitions import ProviderDefinition
from ...providers.winhpc.WinHpcManifestProvider import WinHpcManifestProvider, validate_manifest
from change_doc import JCD
from django.conf import settings


class WinHpcManifestProviderTests(SetupRunMixin, TestCase):
    """
    Unit tests for the WinHpcManifestProvider class.
    """
    def setUp(self):
        """
        Setup a run and its associated user.  Also, create the provider's definition.
        """
        clusters.TestingApi.enable_mock_cluster()
        mock_cluster = clusters.get(clusters.TestingApi.MOCK_CLUSTER_ID)
        self.setup_run()
        self.provider_definition = ProviderDefinition(provider_name.PROTOTYPE, mock_cluster, None)

    def tearDown(self):
        clusters.TestingApi.disable_mock_cluster()

    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.winhpc_submit')
    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.validate_manifest')
    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.app_env.is_production')
    @override_settings(INGESTION_URL="MOCK URL")
    def test_submit(self, mock_is_production, mock_validate_manifest, winhpc_submit):
        self.assertIsNone(self.run.time_launched)
        mock_is_production.return_value = False
        provider = WinHpcManifestProvider(self.provider_definition, self.run, self.user)
        reps_per_exec = 1
        success = provider.submit_jobs(reps_per_exec)
        self.assertTrue(success)
        run = data_services.models.DimRun.objects.get(id=self.run.id)
        self.assertIsNotNone(run.time_launched)
        secrets_dict = {
            "host": "mock",
            "password": "mock",
            "username": "mock"
        }

        script_path = getattr(settings, "JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH", None)
        winhpc_submit.assert_called_with(self.run.id,
                                         self.user.username,
                                         script_path,
                                         secrets_dict["host"],
                                         secrets_dict["username"],
                                         secrets_dict["password"],
                                         'MOCK URL')
        # base_dir = getattr(settings, "JOB_SERVICES_BASE_DIR", None)
        # mock_psc_submit_manifest.assert_called_with(str(self.run.id),
        #                                             self.user.username,
        #                                             secrets_dict,
        #                                             use_prod_site=False,
        #                                             alt_ingest_url="MOCK URL",
        #                                             base_dir=base_dir)
        mock_validate_manifest.assert_called_with(self.run, reps_per_exec)

    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.winhpc_submit')
    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.validate_manifest')
    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.app_env.is_production')
    @override_settings(INGESTION_URL="MOCK URL")
    def test_submit_with_no_success(self, mock_is_production, mock_validate_manifest, mock_winhpc_submit):
        self.assertIsNone(self.run.time_launched)
        mock_is_production.return_value = False
        #mock_psc_submit_manifest.return_value = -1
        mock_winhpc_submit.return_value = -1
        provider = WinHpcManifestProvider(self.provider_definition, self.run, self.user)
        reps_per_exec = 1
        success = provider.submit_jobs(reps_per_exec)
        self.assertFalse(success)
        run = data_services.models.DimRun.objects.get(id=self.run.id)
        self.assertIsNone(run.time_launched)
        secrets_dict = {
            "host": "mock",
            "password": "mock",
            "username": "mock"
        }
        #base_dir = getattr(settings, "JOB_SERVICES_BASE_DIR", None)

        # mock_psc_submit_manifest.assert_called_with(str(self.run.id),
        #                                             self.user.username,
        #                                             secrets_dict,
        #                                             use_prod_site=False,
        #                                             alt_ingest_url="MOCK URL",
        #                                             base_dir=base_dir)
        script_path = getattr(settings, "JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH", None)
        mock_winhpc_submit.assert_called_with(self.run.id,
                                         self.user.username,
                                         script_path,
                                         secrets_dict["host"],
                                         secrets_dict["username"],
                                         secrets_dict["password"],
                                         'MOCK URL')
        mock_validate_manifest.assert_called_with(self.run, reps_per_exec)

    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.winhpc_submit')
    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.validate_manifest')
    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.app_env.is_production')
    @override_settings(INGESTION_URL="MOCK URL")
    def test_submit_wrong_model_version(self, mock_is_production, mock_validate_manifest, mock_winhpc_submit):
        self.assertIsNone(self.run.time_launched)
        mock_is_production.return_value = False
        #mock_psc_submit_manifest.return_value = -1
        mock_winhpc_submit.return_value = -1
        self.run.model_version = "bla-blah"
        self.run.save()
        provider = WinHpcManifestProvider(self.provider_definition, self.run, self.user)
        reps_per_exec = 1
        # model_version = run.model_version

        self.assertRaises(RuntimeError, provider.submit_jobs, reps_per_exec)
        run = data_services.models.DimRun.objects.get(id=self.run.id)
        self.assertIsNone(run.time_launched)


    @override_settings(INGESTION_URL=dict())
    @mock.patch('job_services.providers.winhpc.WinHpcManifestProvider.validate_manifest')
    def test_submit_with_invalid_ingestion_url_type(self, mock_validate_manifest):
        provider = WinHpcManifestProvider(self.provider_definition, self.run, self.user)
        reps_per_exec = 8
        self.assertRaises(TypeError, provider.submit_jobs, reps_per_exec)

    def test_get_run_status(self):
        self.add_executions_and_replications(10)
        provider = WinHpcManifestProvider(self.provider_definition, self.run, self.user)
        status = provider.get_run_status()
        self.assertEqual(status.percent_completed(), 50)
        self.assertEqual(status.percent_failed(), 50)
        self.assertEqual(status.percent_running(), 0)

    def test_validate_manifest_when_valid(self):
        self.run.jcd = JCD()
        validate_manifest(self.run, reps_per_exec=1)