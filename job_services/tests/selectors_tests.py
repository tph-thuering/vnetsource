import mock

from django.test import TestCase

from .. import cluster_id, selectors, clusters
from .data_mixins import SetupRunMixin
from .mocks.mixins import make_mock_factory_provider
from ..providers import provider_name
from ..providers import factories


MOCK_CLUSTER = cluster_id.TestingApi.MOCK_ID


class SelectorTests(SetupRunMixin, TestCase):
    """
    Unit tests for the selectors.
    """
    def setUp(self):
        """
        Create a run for use in the tests.
        """
        self.setup_run()

    def test_select_provider_with_OM_run(self):
        """
        Test the select_provider function with an OpenMalaria run.
        """
        self.run.models_key = self.OM_model
        self.run.save()
        p, message = selectors.select_provider(run=self.run, user=self.user, cluster="string", manifest=True)
        self.assertEqual(message, selectors.OM_SUBMISSION_NOT_SUPPORTED)

    @mock.patch("job_services.selectors.select_cluster_for_run")
    def test_select_provider_when_no_cluster_is_returned(self, mock_select_cluster):
        mock_select_cluster.return_value = None, 'mock message'
        p, message = selectors.select_provider(run=self.run, user=self.user, cluster="string", manifest=False)
        self.assertEqual(p, None)
        self.assertEqual(message, "mock message")

    @mock.patch("job_services.selectors.select_cluster_for_run")
    @mock.patch("job_services.selectors.select_provider_factory")
    def test_select_provider_when_no_factory(self, mock_select_provider_factory, mock_select_cluster):
        message_to_return = "no factory returned, mock"
        cluster_obj = clusters.Cluster(cluster_id.ND_WINDOWS, "mock", "mock", "mock", "mock")
        mock_select_cluster.return_value = cluster_obj, 'mock success message'
        mock_select_provider_factory.return_value = (None, message_to_return)
        p, message = selectors.select_provider(run=self.run, user=self.user, cluster="string", manifest=False)
        self.assertEqual(p, None)
        self.assertEqual(message, message_to_return)

    @mock.patch("job_services.selectors.select_cluster_for_run")
    @mock.patch("job_services.selectors.select_provider_factory")
    def test_select_provider_with_factory(self, mock_select_provider_factory, mock_select_cluster):
        """
        Test the select_provider function when select_provider_factory returns a factory.
        """
        cluster_obj = clusters.Cluster(cluster_id.ND_WINDOWS, "mock", "mock", "mock", "mock")
        mock_select_cluster.return_value = cluster_obj, 'mock success message'
        clusters.TestingApi.enable_mock_cluster()
        message_to_return = "mock factory returned"
        mock_select_provider_factory.return_value = (make_mock_factory_provider(), message_to_return)
        p, message = selectors.select_provider(run=self.run, user=self.user, cluster="string", manifest=True)
        self.assertEqual(message, message_to_return)
        self.assertEqual(p.run, self.run)
        self.assertEqual(p.user, self.user)
        clusters.TestingApi.disable_mock_cluster()

    @mock.patch("job_services.selectors.exceeds_quota")
    def test_select_cluster_for_run_when_cluster_is_specified(self, mock_exceeds_quota):
        """
        Test the select_provider_factory function when the job quota is exceeded.
        """
        clusters.TestingApi.enable_mock_cluster()
        exceeds_quota_message = 'Does not exceed quota'
        mock_exceeds_quota.return_value = (False, exceeds_quota_message)
        cluster, message = selectors.select_cluster_for_run(self.run, self.user, MOCK_CLUSTER)
        self.assertIs(cluster, clusters.get(clusters.TestingApi.MOCK_CLUSTER_ID))
        self.assertEqual(message, selectors.SUCCESS_MESSAGE)

    @mock.patch("job_services.selectors.exceeds_quota")
    def test_select_cluster_for_run_when_cluster_is_default(self, mock_exceeds_quota):
        """
        Test the select_provider_factory function when the job quota is exceeded.
        """
        exceeds_quota_message = 'Does not exceed quota'
        mock_exceeds_quota.return_value = (False, exceeds_quota_message)
        clusters.TestingApi.add_cluster(cluster_id.ND_WINDOWS)
        cluster, message = selectors.select_cluster_for_run(self.run, self.user, cluster_id.AUTO)
        self.assertIs(cluster, clusters.get(cluster_id.ND_WINDOWS))
        self.assertEqual(message, selectors.SUCCESS_MESSAGE)

    @mock.patch("job_services.selectors.exceeds_quota")
    @mock.patch("job_services.clusters.get")
    def test_select_cluster_for_run_when_quota_exceeded(self, mock_clusters_get, mock_exceeds_quota):
        """
        Test the select_provider_factory function when the job quota is exceeded.
        """
        mock_clusters_get.return_value = clusters.Cluster(cluster_id.ND_WINDOWS, "mock", "mock", "mock", "mock")
        exceeds_quota_message = 'Exceeds quota'
        mock_exceeds_quota.return_value = (True, exceeds_quota_message)
        cluster, message = selectors.select_cluster_for_run(self.run, self.user, MOCK_CLUSTER)
        self.assertIsNone(cluster)
        self.assertEqual(message, exceeds_quota_message)

    @mock.patch("job_services.selectors._get_providers_for_cluster")
    def test_select_provider_factory_with_no_providers_for_cluster(self, mock_get_providers):
        """
        Test the select_provider_factory function without the manifest keyword.
        """
        mock_get_providers.return_value = list()
        cluster = clusters.Cluster(cluster_id.ND_WINDOWS, "mock", "mock", "mock", "mock")
        factory, message = selectors.select_provider_factory(cluster, manifest=True)
        self.assertIsNone(factory)
        self.assertEqual(message, selectors.NO_PROVIDERS_FOUND % cluster_id.ND_WINDOWS)

    @mock.patch("job_services.selectors._get_providers_for_cluster")
    @mock.patch("job_services.selectors.factories.get_factory")
    def test_select_provider_factory_with_manifest(self, mock_get_factory, mock_get_providers):
        """
        Test the select_provider_factory function with manifest=True.
        """
        mock_get_providers.return_value = [provider_name.MANIFEST_PROTOTYPE]
        cluster = clusters.Cluster(cluster_id.ND_WINDOWS, "mock", "mock", "mock", "mock")
        factory, message = selectors.select_provider_factory(cluster, manifest=True)
        self.assertIs(factory, mock_get_factory.return_value)
        self.assertEqual(message, provider_name.MANIFEST_PROTOTYPE)
        mock_get_factory.assert_called_with(provider_name.MANIFEST_PROTOTYPE)

    def test_get_providers_for_cluster(self):
        #TODO figure why this was hiding the previous error
        cluster = clusters.Cluster(cluster_id.ND_WINDOWS, "mock", "mock", "mock", "mock")
        provider_names = [name for name, factory in factories._factories.iteritems()]
        self.assertEqual(selectors._get_providers_for_cluster(cluster), provider_names)

        cluster2 = clusters.Cluster(cluster_id.PSC_LINUX, "mock", "mock", "mock", "mock")
        self.assertEqual(selectors._get_providers_for_cluster(cluster2), [])
