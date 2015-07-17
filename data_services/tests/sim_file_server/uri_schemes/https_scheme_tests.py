from mock import patch
import requests.auth

import VECNet.secrets_default

from .conf_tests import ConfigurationTests
from .handler_tests import SchemeHandlerTests
from ....sim_file_server.uri_schemes.https_scheme import (ConfigurationErrors, HttpsSchemeConfiguration,
                                                          HttpsSchemeHandler)


TEST_DIR_URL = 'https://vecnet-qa.crc.nd.edu/webdav/unit-tests/'

PROTECTED_TEST_DIR_URL = 'https://vecnet-qa.crc.nd.edu/webdav/protected/unit-tests/'


class HttpsSchemeHandlerTests(SchemeHandlerTests):
    """
    Tests for the "https:" scheme handler.
    """

    @classmethod
    def setUpClass(cls):
        super(HttpsSchemeHandlerTests, cls).setUpClass()

        HttpsSchemeConfiguration.set_root_directory(TEST_DIR_URL)

    def get_handler(self):
        return HttpsSchemeHandler()


class HttpsSchemeHandlerAuthTests(SchemeHandlerTests):
    """
    Tests for the "https:" scheme handler using basic HTTP authentication.
    """

    @classmethod
    def setUpClass(cls):
        super(HttpsSchemeHandlerAuthTests, cls).setUpClass()

        settings = {
            'root directory': PROTECTED_TEST_DIR_URL,
            'authentication': 'basic',
            'username': VECNet.secrets_default.WebDavServer.USERNAME,
            'password': VECNet.secrets_default.WebDavServer.PASSWORD,
            'verify certificates': False,
        }
        HttpsSchemeConfiguration().load_settings(settings)

    def get_handler(self):
        return HttpsSchemeHandler()

    @classmethod
    def tearDownClass(cls):
        super(HttpsSchemeHandlerAuthTests, cls).tearDownClass()
        HttpsSchemeConfiguration().reset_settings()


class HttpsSchemeConfTests(ConfigurationTests):
    """
    Tests of the handling of the https-scheme configuration settings.
    """

    def setUp(self):
        self.https_scheme_conf = HttpsSchemeConfiguration()

    def tearDown(self):
        self.https_scheme_conf.reset_settings()

    def test_settings_not_dict(self):
        """
        Test when the file scheme settings is not a dictionary.
        """
        settings = 'should be a dictionary'
        self.assertConfigurationError(ConfigurationErrors.NOT_DICT, self.https_scheme_conf.load_settings,
                                      settings)

    def test_no_directory_setting(self):
        """
        Test when the file scheme settings is missing the 'root directory' key.
        """
        settings = {
            'foo': 'bar',
        }
        self.assertConfigurationError(ConfigurationErrors.NO_DIRECTORY, self.https_scheme_conf.load_settings,
                                      settings)

    def test_directory_not_str(self):
        """
        Test when the 'root directory' setting is not a string.
        """
        settings = {
            'root directory': -7,
        }
        self.assertConfigurationError(ConfigurationErrors.DIRECTORY_NOT_STR, self.https_scheme_conf.load_settings,
                                      settings)

    def test_directory_not_exist(self):
        """
        Test when the 'root directory' setting is a path that doesn't exist.
        """
        settings = {
            'root directory': TEST_DIR_URL + 'SubFolderThatDoesNotExist/',
        }
        self.assertConfigurationError(ConfigurationErrors.ROOT_DIR_NOT_EXIST, self.https_scheme_conf.load_settings,
                                      settings)

    def test_valid_directory(self):
        """
        Test when the 'root directory' setting is a valid value.
        """
        settings = {
            'root directory': TEST_DIR_URL,
        }
        self.https_scheme_conf.load_settings(settings)
        self.assertEqual(HttpsSchemeConfiguration.root_directory, TEST_DIR_URL)

    def test_verify_not_bool(self):
        """
        Test when the 'verify certificates' setting is not a boolean.
        """
        settings = {
            'root directory': TEST_DIR_URL,
            'verify certificates': 3.14,
        }
        self.assertConfigurationError(ConfigurationErrors.VERIFY_NOT_BOOL, self.https_scheme_conf.load_settings,
                                      settings)

    @patch('data_services.sim_file_server.uri_schemes.https_scheme.directory_exists')
    def test_verify_true(self, mock_directory_exists):
        """
        Test when the 'verify certificates' setting is True.
        """
        settings = {
            'root directory': TEST_DIR_URL,
            'verify certificates': True,
        }
        mock_directory_exists.return_value = True
        self.https_scheme_conf.load_settings(settings)
        self.assertTrue(HttpsSchemeConfiguration.verify_certificates)

    def test_no_authentication(self):
        """
        Test when the 'authentication' setting is not present (it's optional).
        """
        settings = {
        }
        auth = self.https_scheme_conf.load_authentication_settings(settings)
        self.assertIsNone(auth)

    def test_unknown_auth(self):
        """
        Test when the 'authentication' setting is an unknown value.
        """
        settings = {
            'authentication': 'Foo'
        }
        self.assertConfigurationError(ConfigurationErrors.UNKNOWN_AUTH,
                                      self.https_scheme_conf.load_authentication_settings,
                                      settings)

    def test_basic_auth_no_username(self):
        """
        Test when the 'username' setting is missing for basic HTTP authentication.
        """
        settings = {
            'authentication': 'basic',
        }
        self.assertConfigurationError(ConfigurationErrors.NO_USERNAME,
                                      self.https_scheme_conf.load_authentication_settings,
                                      settings)

    def test_basic_auth_username_not_str(self):
        """
        Test when the 'username' setting for basic HTTP authentication is not a string.
        """
        settings = {
            'authentication': 'basic',
            'username': True,
        }
        self.assertConfigurationError(ConfigurationErrors.USERNAME_NOT_STR,
                                      self.https_scheme_conf.load_authentication_settings,
                                      settings)

    def test_basic_auth_no_password(self):
        """
        Test when the 'password' setting is missing for basic HTTP authentication.
        """
        settings = {
            'authentication': 'basic',
            'username': 'test-user',
        }
        self.assertConfigurationError(ConfigurationErrors.NO_PASSWORD,
                                      self.https_scheme_conf.load_authentication_settings,
                                      settings)

    def test_basic_auth_password_not_str(self):
        """
        Test when the 'password' setting for basic HTTP authentication is not a string.
        """
        settings = {
            'authentication': 'basic',
            'username': 'test-user',
            'password': -1.23,
        }
        self.assertConfigurationError(ConfigurationErrors.PASSWORD_NOT_STR,
                                      self.https_scheme_conf.load_authentication_settings,
                                      settings)

    def test_basic_auth(self):
        """
        Test when basic HTTP authentication is properly configured.
        """
        settings = {
            'authentication': 'basic',
            'username': 'test-user',
            'password': 'Secret',
        }
        auth = self.https_scheme_conf.load_authentication_settings(settings)
        self.assertIsInstance(auth, requests.auth.HTTPBasicAuth)
        self.assertEqual(auth.username, settings['username'])
        self.assertEqual(auth.password, settings['password'])

    def test_protected_dir(self):
        """
        Test when basic HTTP authentication is properly configured for protected test directory.
        """
        settings = {
            'root directory': PROTECTED_TEST_DIR_URL,
            'authentication': 'basic',
            'username': VECNet.secrets_default.WebDavServer.USERNAME,
            'password': VECNet.secrets_default.WebDavServer.PASSWORD,
            'verify certificates': False,
        }
        self.https_scheme_conf.load_settings(settings)
        self.assertEqual(HttpsSchemeConfiguration.root_directory, PROTECTED_TEST_DIR_URL)
