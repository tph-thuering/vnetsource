"""
Configuration of Job Services
"""
import docs.sphinx
import sys
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from . import clusters, conf_err, quotas
from . import dispatcher_conf
import providers.conf


class Keys(object):
    """
    Keys that are required in the JOB_SERVICES setting dictionary
    """
    CLUSTERS = 'clusters'
    DEFAULT_QUOTAS = 'default quotas'
    PROVIDERS = 'providers'
    DISPATCHER = 'dispatcher'


_is_required = {
    Keys.CLUSTERS: True,
    Keys.DEFAULT_QUOTAS: True,
    Keys.PROVIDERS: True,
    Keys.DISPATCHER: False,
}


class MissingKeyError(conf_err.ConfigurationError):
    """
    A required key is missing from JOB_SERVICES setting
    """
    ERROR_CODE = 'JOB_SERVICES missing key'

    def __init__(self, key):
        super(MissingKeyError, self).__init__('JOB_SERVICES setting does not have "%s" key' % key,
                                              MissingKeyError.ERROR_CODE)
        self.key = key


def configure_component():
    """
    Configure the job-services component by loading its settings.  This function is called in the dispatcher module
    to ensure the settings have been loaded before any caller uses the dispatcher's API functions.  The settings are
    loaded only if the Django project is running.
    """
    # Don't load settings if generating documentation with Sphinx
    if docs.sphinx.is_running:
        return

    # Don't load settings if running tests
    if 'test' in sys.argv:
        return

    load_settings()


def load_settings():
    """
    Load the component's settings from the Django project settings.
    """
    if not hasattr(settings, 'JOB_SERVICES'):
        raise ImproperlyConfigured('JOB_SERVICES setting is not defined')

    module_initializers = (
        (Keys.DEFAULT_QUOTAS, quotas.load_defaults),
        (Keys.CLUSTERS, clusters.initialize),
        (Keys.PROVIDERS, providers.conf.initialize_providers),
        (Keys.DISPATCHER, dispatcher_conf.load_selector)
    )
    for (key, initializer) in module_initializers:
        if key not in settings.JOB_SERVICES:
            if _is_required[key]:
                raise MissingKeyError(key)
            else:
                # Optional key, so go to next key
                continue  # pragma: no cover -- This line is excluded due to a coverage.py bug. See the post below:
                          # https://bitbucket.org/ned/coveragepy/issue/198/continue-marked-as-not-covered
        try:
            initializer(settings.JOB_SERVICES[key])
        except conf_err.ConfigurationError, exc:
            if exc.error_code == conf_err.ConfigurationErrorCodes.SETTINGS_TYPE:
                expected_type = exc.message
                raise conf_err.ConfigurationError('wrong type for "%s" key: %s' % (key, expected_type), exc.error_code)
            else:
                raise exc


def reset_settings():
    """
    Reset all the component's settings.  Used for teardown in unit tests.
    """
    providers.conf.delete_all()
    clusters.delete_all()