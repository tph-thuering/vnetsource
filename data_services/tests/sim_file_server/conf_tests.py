from django.conf import ImproperlyConfigured, settings
from django.test import TestCase

from ...sim_file_server import conf
from ...sim_file_server.api import FileServer
from ...sim_file_server.uri_schemes.file_scheme import FileSchemeConfiguration
from ...sim_file_server.uri_schemes.https_scheme import HttpsSchemeConfiguration


class ConfigurationTests(TestCase):
    """
    Base class for configuration tests.
    """

    def assertImproperlyConfigured(self, expected_arg0, callable_obj, *args, **kwargs):
        """
        Assert that an ImproperlyConfigured exception is raised when an object is called.

        :param expected_arg0: The object that should be the first argument (i.e., args[0]) of the exception.
        """
        try:
            callable_obj(*args, **kwargs)
            self.fail('Expected ImproperlyConfigured, but no exception raised')
        except ImproperlyConfigured, exc:
            self.assertIs(expected_arg0, exc.args[0])
        except Exception, exc:
            self.fail('Expected ImproperlyConfigured, but got %s' % repr(exc))


class ServerConfTests(ConfigurationTests):
    """
    Tests of the server-level configuration settings.
    """

    def setUp(self):
        # Reset the configuration to its initial state.
        conf.TestingAPI.reset_configuration()

    def test_no_uri_schemes(self):
        """
        Test when there is no 'URI schemes' key in the server settings.
        """
        file_server_settings = {
            'write scheme': 'data',
        }
        with self.settings(FILE_SERVER=file_server_settings):
            self.assertImproperlyConfigured(conf.Errors.NO_URI_SCHEMES, conf.get_active_server)

    def test_unknown_scheme(self):
        """
        Test when there is an unknown scheme in the 'URI schemes' setting.
        """
        file_server_settings = {
            'URI schemes': ('data', 'foo-bar'),
        }
        with self.settings(FILE_SERVER=file_server_settings):
            self.assertImproperlyConfigured(conf.Errors.UNKNOWN_SCHEME, conf.get_active_server)
            self.assertEqual(conf.Errors.UNKNOWN_SCHEME.description.placeholders, {'name': 'foo-bar'})

    def test_no_write_scheme(self):
        """
        Test when there is no 'write scheme' key in the server settings.
        """
        file_server_settings = {
            'URI schemes': ('data',),
        }
        with self.settings(FILE_SERVER=file_server_settings):
            self.assertImproperlyConfigured(conf.Errors.NO_WRITE_SCHEME, conf.get_active_server)

    def test_no_file_settings(self):
        """
        Test when there are no file scheme settings in the server settings.
        """
        file_server_settings = {
            'URI schemes': ('file', ),
            'write scheme': 'file',
        }
        with self.settings(FILE_SERVER=file_server_settings):
            self.assertImproperlyConfigured(conf.Errors.NO_FILE_SCHEME_SETTINGS, conf.get_active_server)

    def test_no_https_settings(self):
        """
        Test when there are no https scheme settings in the server settings.
        """
        file_server_settings = {
            'URI schemes': ('https', ),
            'write scheme': 'https',
        }
        with self.settings(FILE_SERVER=file_server_settings):
            self.assertImproperlyConfigured(conf.Errors.NO_HTTPS_SCHEME_SETTINGS, conf.get_active_server)

    def test_default_settings(self):
        """
        Test that the default settings in VECNet.settings are valid.
        """
        with self.settings():
            server = conf.get_active_server()
            self.assertIsInstance(server, FileServer)
            file_server_settings = settings.FILE_SERVER
            self.assertEqual(FileSchemeConfiguration.root_directory,
                             file_server_settings['file scheme']['root directory'])
            self.assertEqual(HttpsSchemeConfiguration.root_directory,
                             file_server_settings['https scheme']['root directory'])
