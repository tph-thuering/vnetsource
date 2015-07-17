"""
Mixin classes for configuration error testing.
"""

from unittest import TestCase
from ..conf_err import ConfigurationError


class ConfigurationErrorMixin(TestCase):
    """
    Mixin for test suites that will check if ConfigurationError exception is raised.
    """

    def assertRaisesConfError(self, expected_error_code, callable_obj, *args):
        """
        Assert that a callable raises a ConfigurationError with a particular code.
        """
        try:
            callable_obj(*args)
            self.fail('Expected ConfigurationError, but no exception raised')
        except ConfigurationError, exc:
            self.assertEqual(expected_error_code, exc.error_code)
        except Exception, exc:
            self.fail('Expected ConfigurationError, but got %s' % repr(exc))
