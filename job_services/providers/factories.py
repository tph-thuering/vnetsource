"""
Factories for making provider instances (objects).
"""

from .definitions import ProviderDefinition


class Factory(object):
    """
    Factory for making instances of a particular provider.
    """
    def __init__(self, provider_class, provider_definition):
        self.provider_class = provider_class
        assert isinstance(provider_definition, ProviderDefinition)
        self.provider_definition = provider_definition

    def create_provider(self, run, user):
        return self.provider_class(self.provider_definition, run, user)


_factories = dict()


def register(factory):
    """
    Register the factory for a particular provider, for subsequent retrieval by the provider's name.

    :param Factory factory: The factory for creating a particular type of provider.
    """
    assert isinstance(factory, Factory)
    _factories[factory.provider_definition.name] = factory


def get_factory(provider_name):
    """
    Get the factory function for a provider.

    :returns: A :py:class:`~job_services.providers.factories.Factory` object or None.
    """
    return _factories.get(provider_name, None)


def unregister_all():
    """
    Unregister all the factories.  Used for tear down in unit tests.
    """
    global _factories
    _factories = dict()