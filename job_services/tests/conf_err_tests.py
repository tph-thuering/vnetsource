from django.test import TestCase
from ..conf_err import ConfigurationError, ConfigurationErrorCodes


class ConfErrTests(TestCase):
    """
    Unit tests for the conf_err module.
    """
    def test_configuration_error(self):
        """
        Test the ConfigurationError class.
        """
        error = ConfigurationError("Test message.")
        self.assertEqual(error.message, "Test message.")
        self.assertEqual(error.error_code, None)
        self.assertEqual(error.__str__(), "Test message.")
        error = ConfigurationError("Test message.", "Test code.")
        self.assertEqual(error.message, "Test message.")
        self.assertEqual(error.error_code, "Test code.")
        self.assertEqual(error.__str__(), "Test message.")

    def test_configuration_error_codes(self):
        """
        Test the ConfigurationErrorCodes class.
        """
        codes = ConfigurationErrorCodes()
        self.assertEqual(codes.SETTINGS_TYPE, 'settings: wrong type')