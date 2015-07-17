from .providers.conf import parse_callable
from . import conf_err
from .conf_err import ConfigurationError
from . import selectors


class ConfigurationErrorCodes(object):
    """
    Configuration codes.
    """
    PROVIDER_NOT_STRING = 'provider selector: not string'


selection_algorithm = selectors.select_provider

def load_selector(settings):
    if not isinstance(settings, dict):
        raise ConfigurationError('expected dict', conf_err.ConfigurationErrorCodes.SETTINGS_TYPE)
    global selection_algorithm
    algorithm_name = settings.get('provider selector', None)
    if algorithm_name is None:
        return
    if not isinstance(algorithm_name, basestring):
        raise ConfigurationError('%s is not a string' % algorithm_name, ConfigurationErrorCodes.PROVIDER_NOT_STRING)
    selection_algorithm = parse_callable(algorithm_name)