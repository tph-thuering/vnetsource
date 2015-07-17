from ...providers.definitions import ProviderDefinition
from ... import clusters
from unittest import TestCase


class ProviderDefinitionTests(TestCase):
    """
    Tests for the ProviderDefinition class.
    """
    def setUp(self):
        clusters.TestingApi.enable_mock_cluster()

    def tearDown(self):
        clusters.TestingApi.disable_mock_cluster()

    def test_non_dict_for_aux_params_raises_error(self):
        self.assertRaises(AssertionError, ProviderDefinition, "name", "", "sim model", 1)
        self.assertRaises(AssertionError, ProviderDefinition, "name", "", "sim model", "")
        self.assertRaises(AssertionError, ProviderDefinition, "name", "", "sim model", list())
        self.assertRaises(AssertionError, ProviderDefinition, "name", "", "sim model", tuple())
        ProviderDefinition("name", clusters.get(clusters.TestingApi.MOCK_CLUSTER_ID), "sim_model", None)
        ProviderDefinition("name", clusters.get(clusters.TestingApi.MOCK_CLUSTER_ID), "sim_model", {"param": "value"})

    def test_non_valid_cluster_raises_error(self):
        self.assertRaises(AssertionError, ProviderDefinition, "name", "", "sim model", None)
        self.assertRaises(AssertionError, ProviderDefinition, "name", list(), "sim model", None)
        self.assertRaises(AssertionError, ProviderDefinition, "name", dict(), "sim model", None)
        self.assertRaises(AssertionError, ProviderDefinition, "name", tuple(), "sim model", None)
        self.assertRaises(AssertionError, ProviderDefinition, "name", 21, "sim model", None)
        ProviderDefinition("name", clusters.get(clusters.TestingApi.MOCK_CLUSTER_ID), "sim_model", None)