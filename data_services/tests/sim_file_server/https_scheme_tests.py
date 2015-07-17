from abc import ABCMeta

import VECNet.secrets_default

from .server_tests import FileServerTests
from .uri_schemes.https_scheme_tests import PROTECTED_TEST_DIR_URL, TEST_DIR_URL
from ...sim_file_server.multi_scheme import MultiSchemeServer
from ...sim_file_server.uri_schemes.https_scheme import HttpsSchemeConfiguration


class HttpsSchemeServerTests(FileServerTests):
    """
    Base class for tests of the sim file server configured for just the "https:" scheme for reading and writing.
    """
    __metaclass__ = ABCMeta

    def test_data_uri(self):
        """
        Test that the server raises an error with a "data:" URI.
        """
        file_server = self.get_server()
        self.assertRaises(ValueError, file_server.open_for_reading, 'data:,Hello World')

    def test_file_uri(self):
        """
        Test that the server raises an error with a "file:" URI.
        """
        file_server = self.get_server()
        self.assertRaises(ValueError, file_server.open_for_reading, 'file:///foo/bar.txt')


class HttpsSchemeServerTestsNoAuth(HttpsSchemeServerTests):
    """
    Tests with a sim file server that uses no authentication.
    """

    @classmethod
    def setUpClass(cls):
        super(HttpsSchemeServerTestsNoAuth, cls).setUpClass()

        HttpsSchemeConfiguration().load_settings({'root directory': TEST_DIR_URL})
        cls._server = MultiSchemeServer(('https',), 'https')

    def get_server(self):
        return self._server


class HttpsSchemeServerTestsWithAuth(HttpsSchemeServerTests):
    """
    Tests with a sim file server configured with authentication.
    """

    @classmethod
    def setUpClass(cls):
        super(HttpsSchemeServerTestsWithAuth, cls).setUpClass()

        settings = {
            'root directory': PROTECTED_TEST_DIR_URL,
            'authentication': 'basic',
            'username': VECNet.secrets_default.WebDavServer.USERNAME,
            'password': VECNet.secrets_default.WebDavServer.PASSWORD,
            'verify certificates': False,
        }
        HttpsSchemeConfiguration().load_settings(settings)
        cls._server = MultiSchemeServer(('https',), 'https')

    def get_server(self):
        return self._server
