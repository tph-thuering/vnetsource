"""
Configuration of job-service providers
"""

import importlib
import inspect
import re

from .base import ProviderBase
from .factories import Factory, get_factory, register, unregister_all
from .definitions import ProviderDefinition
from .. import cluster_id, conf_err, clusters
from ..conf_err import ConfigurationError
from simulation_models import model_id

REQUIRED_KEYS = ['name', 'cluster', 'model', 'class']


class ConfigurationErrorCodes(object):
    # errors with the fullname of a provider's class
    BAD_CALLABLE_NAME = 'callable: bad identifier'
    MODULE_IMPORT_ERROR = 'class: import error'
    NO_MODULE = 'callable: no module'
    NO_CALLABLE_NAME = 'callable: no name'
    NOT_PY_CALLABLE = 'callable: not Python callable'
    NOT_PY_CLASS = 'class: not Python class'
    NOT_SUBCLASS = 'class: not derived from ProviderBase'
    UNDEFINED_CALLABLE = 'callable: undefined'

    # errors with an individual provider's settings
    BAD_CLUSTER = 'settings: bad cluster'
    BAD_MODEL = 'settings: bad model'
    CLASS_NOT_STRING = 'settings: class not string'
    CLUSTER_NOT_STRING = 'settings: cluster not string'
    DUPLICATE_NAME = 'settings: duplicate name'
    MODEL_NOT_STRING = 'settings: model not string'
    NAME_NOT_STRING = 'settings: name not string'
    NO_CLASS_KEY = 'settings: class missing'
    NO_CLUSTER_KEY = 'settings: cluster missing'
    NO_MODEL_KEY = 'settings: model missing'
    NO_NAME_KEY = 'settings: name missing'
    NOT_DICTIONARY = 'settings: not dictionary'
    UNCONFIGURED_CLUSTER = "settings: cluster is not configured"

    # errors with the list of settings for multiple providers
    NO_PROVIDERS = 'no providers'


def initialize_providers(settings):
    """
    Initialize the providers by loading their configuration settings.  The providers are specified in a tuple of
    definitions, where each definition is a dictionary.  For example::

        (
            {
                'name' : 'prototype',
                'cluster' : cluster_id.PSC_WINDOWS,
                'class' : 'job_services.providers.WinHpcProvider.WinHpcProvider',
                # all other keys are considered specific to the particular provider class
            },
            {
                'name' : 'manifest prototype',
                'cluster' : cluster_id.PSC_WINDOWS,
                'class' : 'job_services.providers.WinHpcManifestProvider.WinHpcManifestProvider',
                # class-specific keys ...
            },
            ...
        )
    """
    if not isinstance(settings, tuple):
        raise ConfigurationError('expected tuple', conf_err.ConfigurationErrorCodes.SETTINGS_TYPE)
    if len(settings) == 0:
        raise ConfigurationError('no job-services providers configured', ConfigurationErrorCodes.NO_PROVIDERS)
    for settings_dict in settings:
        initialize_provider(settings_dict)


def initialize_provider(settings):
    """
    Initialize a specific provider.

    These keys are required in the settings dictionary:

    * "name" : The provider's name (*str*).
    * "cluster" : ID of the cluster that the provider submits jobs to (*str*).
    * "class" : Fully-qualified name of the Python class that implements the provider (*str*).

    :param dict settings: The provider's configuration settings.

    :raises: ConfigurationError
    """
    if not isinstance(settings, dict):
        raise ConfigurationError('settings parameter is not a dictionary', ConfigurationErrorCodes.NOT_DICTIONARY)

    try:
        provider_name = settings["name"]
    except KeyError:
        raise ConfigurationError('settings has no "name" key', ConfigurationErrorCodes.NO_NAME_KEY)
    if not isinstance(provider_name, basestring):
        raise ConfigurationError('value for "name" key is not string', ConfigurationErrorCodes.NAME_NOT_STRING)
    if get_factory(provider_name) is not None:
        raise ConfigurationError('provider "%s" already configured' % provider_name,
                                 ConfigurationErrorCodes.DUPLICATE_NAME)

    try:
        cluster = settings["cluster"]
    except KeyError:
        raise ConfigurationError('settings for provider "%s" has no "cluster" key' % provider_name,
                                 ConfigurationErrorCodes.NO_CLUSTER_KEY)
    if not isinstance(cluster, basestring):
        raise ConfigurationError('cluster for provider "%s" is not string' % provider_name,
                                 ConfigurationErrorCodes.CLUSTER_NOT_STRING)
    if not cluster_id.is_valid(cluster):
        raise ConfigurationError('unknown cluster for provider "%s"' % provider_name,
                                 ConfigurationErrorCodes.BAD_CLUSTER)
    cluster_obj = clusters.get(cluster)
    if cluster_obj is None:
        raise ConfigurationError('unconfigured cluster %s' % cluster, ConfigurationErrorCodes.UNCONFIGURED_CLUSTER)

    try:
        class_name = settings["class"]
    except KeyError:
        raise ConfigurationError('settings for provider "%s" has no "class" key' % provider_name,
                                 ConfigurationErrorCodes.NO_CLASS_KEY)
    if not isinstance(class_name, str):
        raise ConfigurationError('class for provider "%s" is not string' % provider_name,
                                 ConfigurationErrorCodes.CLASS_NOT_STRING)

    try:
        simulation_model = settings["model"]
    except KeyError:
        raise ConfigurationError('settings for provider "%s" has no "model" key' % provider_name,
                                 ConfigurationErrorCodes.NO_MODEL_KEY)
    if not isinstance(simulation_model, str):
        raise ConfigurationError('model for provider "%s" is not string' % provider_name,
                                 ConfigurationErrorCodes.MODEL_NOT_STRING)
    if not model_id.is_valid(simulation_model):
        raise ConfigurationError('unknown model for provider "%s"' % provider_name,
                                 ConfigurationErrorCodes.BAD_MODEL)

    optional_settings = get_optional_settings(settings, REQUIRED_KEYS)
    provider_def = ProviderDefinition(provider_name, cluster_obj, simulation_model, optional_settings)
    provider_class = parse_class(class_name)
    provider_factory = Factory(provider_class, provider_def)
    register(provider_factory)


def get_optional_settings(settings, required_keys):
    """
    Return the settings dictionary with the required keys removed.
    :param settings: Provider settings dictionary.
    :param required_keys: A list of keys required for a provider.
    :return: dict
    """
    assert isinstance(settings, dict)
    assert isinstance(required_keys, list)
    return_dict = settings.copy()
    for item in required_keys:
        if item in return_dict:
            del return_dict[item]
    return return_dict


def parse_name(fullname):
    """
    Parse the name of the Python callable (class or function) for a job-services provider.

    :param str fullname: The full name of the callable (e.g., 'package.subpackage.module.FooProvider').

    :returns class: The Python class for the provider.
    :raises ConfigurationError: if the class name is
    """
    fullname_parts = fullname.split('.')
    callable_name = fullname_parts[-1]  # Last part
    if callable_name == '':
        raise ConfigurationError('no callable name in "%s"' % fullname, ConfigurationErrorCodes.NO_CALLABLE_NAME)
    elif not valid_python_identifier(callable_name):
        raise ConfigurationError('callable name "%s" is invalid Python identifier' % callable_name,
                                 ConfigurationErrorCodes.BAD_CALLABLE_NAME)

    module_fullname = '.'.join(fullname_parts[:-1])  # All but the last part (which is the class name)
    if module_fullname == '':
        raise ConfigurationError('no module in "%s"' % fullname, ConfigurationErrorCodes.NO_MODULE)
    try:
        provider_module = importlib.import_module(module_fullname)
    except ImportError:
        raise ConfigurationError('cannot import provider module "%s"' % module_fullname,
                                 ConfigurationErrorCodes.MODULE_IMPORT_ERROR)

    try:
        callable_obj = getattr(provider_module, callable_name)
    except AttributeError:
        raise ConfigurationError('callable "%s" is not defined in "%s"' % (callable_name, module_fullname),
                                 ConfigurationErrorCodes.UNDEFINED_CALLABLE)

    return callable_obj


def parse_class(fullname):
    """
    Given the full path of a class as a string, return the class itself.
    :param fullname: Path to class.
    :return: Python class.
    """
    provider_class = parse_name(fullname)
    if not inspect.isclass(provider_class):
        raise ConfigurationError('%s is not a class' % fullname, ConfigurationErrorCodes.NOT_PY_CLASS)
    if not issubclass(provider_class, ProviderBase):
        raise ConfigurationError('%s is not subclass of ProviderBase' % fullname, ConfigurationErrorCodes.NOT_SUBCLASS)
    return provider_class


def parse_callable(fullname):
    """
    Check if a string is callable.
    :param str fullname: Path to callable.
    :return: Python callable.
    """
    callable_object = parse_name(fullname)
    if not callable(callable_object):
        raise ConfigurationError('%s is not a callable object' % fullname, ConfigurationErrorCodes.NOT_PY_CALLABLE)
    return callable_object


def valid_python_identifier(text):
    """
    Is a string a valid Python identifier?

    :param str text: Text string to be checked
    :returns bool: True if the text is a valid Python identifier; False otherwise.
    """
    identifier_pattern = re.compile(r"^[^\d\W]\w*\Z")
    return identifier_pattern.match(text) is not None


def delete_all():
    """
    Delete all the providers.  Used for tear down in unit tests.
    """
    unregister_all()