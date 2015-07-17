"""
Mixin classes for testing errors.
"""

import unittest

from .errors import CallerError


class CallerErrorMixin(unittest.TestCase):
    """
    Mixin for test suites that will check for CallerError objects when AssertionErrors are raised.
    """

    def assertCallerError(self, expected_arg0, callable_obj, *args, **kwargs):
        """
        Assert that a callable raises an AssertionError with a particular argument.

        :param expected_arg0: The expected value for the AssertionError instance's first argument
                              (i.e., instance.args[0]).
        """
        try:
            callable_obj(*args, **kwargs)
            self.fail('Expected AssertionError, but no exception raised')
        except AssertionError, exc:
            self.assertEqual(exc.args[0], expected_arg0)
        except Exception, exc:
            self.fail('Expected AssertionError, but got %s' % repr(exc))