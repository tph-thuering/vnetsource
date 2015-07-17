from unittest import TestCase

from ....sim_file_server.uri_schemes.conf import ConfigurationError


class ConfigurationTests(TestCase):
    """
    Base class for configuration tests.
    """

    def assertConfigurationError(self, expected_arg0, callable_obj, *args, **kwargs):
        """
        Assert that a ConfigurationError exception is raised when an object is called.

        :param expected_arg0: The object that should be the first argument (i.e., args[0]) of the exception.
        """
        try:
            callable_obj(*args, **kwargs)
            self.fail('Expected ConfigurationError, but no exception raised')
        except ConfigurationError, exc:
            self.assertIs(expected_arg0, exc.args[0])
        except Exception, exc:
            self.fail('Expected ConfigurationError, but got %s' % repr(exc))
