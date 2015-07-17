"""
Mixin classes for test suites that use mocks.
"""

from django.test import TestCase

from .mock_provider import MockProvider
from ... import cluster_id, dispatcher, clusters
from ...providers import definitions, factories, provider_name


MOCK_CLUSTER = cluster_id.TestingApi.MOCK_ID
MOCK_PROVIDER = provider_name.TestingApi.MOCK_NAME


class MockProviderMixin(TestCase):
    """
    Mixin for test suites that use the mock provider.
    """

    def enable_mock_provider(self):
        """
        Enable the mock provider by registering its factory.
        """
        clusters.TestingApi.enable_mock_cluster()
        factories.register(make_mock_factory_provider())
        dispatcher.TestingApi.set_selection_algorithm(MockProviderMixin.mock_selection_algorithm)

    @staticmethod
    def mock_selection_algorithm(run, user, cluster=cluster_id.AUTO, manifest=False):
        """
        Use mock provider if mock cluster specified.  Otherwise, call the default selection algorithm.
        """
        if cluster == MOCK_CLUSTER:
            factory = factories.get_factory(MOCK_PROVIDER)
            assert factory is not None, "Must enable mock provider before creating it"
            provider = factory.create_provider(run, user)
            return provider, MOCK_PROVIDER
        else:
            return dispatcher.DEFAULT_SELECTION_ALGORITHM(run, user, cluster, manifest)

    def disable_mock_provider(self):
        dispatcher.TestingApi.set_selection_algorithm(dispatcher.DEFAULT_SELECTION_ALGORITHM)
        # TODO: unregister the factory for MOCK_PROVIDER
        clusters.TestingApi.disable_mock_cluster()


def make_mock_factory_provider():
    """
    Create a factory for the mock provider.
    """
    mock_cluster = clusters.get(clusters.TestingApi.MOCK_CLUSTER_ID)
    mock_provider_definition = definitions.ProviderDefinition(MOCK_PROVIDER, mock_cluster, None)
    mock_factory = factories.Factory(MockProvider, mock_provider_definition)
    return mock_factory