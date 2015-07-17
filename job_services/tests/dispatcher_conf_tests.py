from unittest import TestCase
from .conf_err_mixins import ConfigurationErrorMixin
from ..dispatcher_conf import load_selector, ConfigurationErrorCodes
from .. import dispatcher_conf
from .. import conf_err


class DispatcherInitializationTests(ConfigurationErrorMixin, TestCase):
    """
    Unit tests for the load_selector function.
    """
    def test_load_selector_with_bad_type(self):
        """
        Test the load_selector function with parameters that are not dictionaries.
        """
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, load_selector, None)
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, load_selector, 'foo')
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, load_selector, 3.14)
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, load_selector, object())
        self.assertRaisesConfError(conf_err.ConfigurationErrorCodes.SETTINGS_TYPE, load_selector, [-1, '', None])

    def test_default_provider_value(self):
        """
        Make sure the default provider is returned when None is passed to the dictionary.
        """
        value_before = dispatcher_conf.selection_algorithm
        load_selector({'provider selector': None})
        value_after = dispatcher_conf.selection_algorithm
        self.assertEqual(value_after, value_before)

    def test_load_selector_with_nonstring_name(self):
        """
        Test the load_selector function with settings parameters where the "provider selector" key has non-string value.
        """
        self.assertRaisesConfError(ConfigurationErrorCodes.PROVIDER_NOT_STRING, load_selector,
                                   {'provider selector': -1})
        self.assertRaisesConfError(ConfigurationErrorCodes.PROVIDER_NOT_STRING, load_selector,
                                   {'provider selector': dict()})