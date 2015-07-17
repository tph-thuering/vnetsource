import os

from .conf_tests import ConfigurationTests
from .handler_tests import SchemeHandlerTests
from ..test_util import OutputDirMixin
from ....sim_file_server.uri_schemes.file_scheme import ConfigurationErrors, FileSchemeConfiguration, FileSchemeHandler


class FileSchemeHandlerTests(SchemeHandlerTests, OutputDirMixin):
    """
    Tests for the "file:" scheme handler.
    """

    @classmethod
    def setUpClass(cls):
        super(FileSchemeHandlerTests, cls).setUpClass()

        FileSchemeConfiguration().load_settings({'root directory': cls.get_output_dir()})
        cls.clean_output_dir()

    def get_handler(self):
        return FileSchemeHandler()


class FileSchemeConfTests(ConfigurationTests):
    """
    Tests of the handling of the file-scheme configuration settings.
    """

    def setUp(self):
        self.file_scheme_conf = FileSchemeConfiguration()

    def tearDown(self):
        self.file_scheme_conf.reset_settings()

    def test_settings_not_dict(self):
        """
        Test when the file scheme settings is not a dictionary.
        """
        settings = 'should be a dictionary'
        self.assertConfigurationError(ConfigurationErrors.NOT_DICT, self.file_scheme_conf.load_settings,
                                        settings)

    def test_no_directory_setting(self):
        """
        Test when the file scheme settings is missing the 'root directory' key.
        """
        settings = {
            'foo': 'bar',
        }
        self.assertConfigurationError(ConfigurationErrors.NO_DIRECTORY, self.file_scheme_conf.load_settings,
                                        settings)

    def test_directory_not_str(self):
        """
        Test when the 'root directory' setting is not a string.
        """
        settings = {
            'root directory': -7,
        }
        self.assertConfigurationError(ConfigurationErrors.DIRECTORY_NOT_STR, self.file_scheme_conf.load_settings,
                                        settings)

    def test_directory_not_exist(self):
        """
        Test when the 'root directory' setting is a path that doesn't exist.
        """
        this_dir = os.path.dirname(__file__)
        settings = {
            'root directory': os.path.join(this_dir, 'SubFolderThatDoesNotExist'),
        }
        self.assertConfigurationError(ConfigurationErrors.ROOT_DIR_NOT_EXIST, self.file_scheme_conf.load_settings,
                                        settings)

    def test_path_is_not_dir(self):
        """
        Test when the 'root directory' setting is a path that isn't a directory.
        """
        settings = {
            'root directory': __file__,
        }
        self.assertConfigurationError(ConfigurationErrors.ROOT_NOT_DIR, self.file_scheme_conf.load_settings,
                                        settings)

    def test_valid_directory(self):
        """
        Test when the 'root directory' setting is a valid value.
        """
        this_dir = os.path.dirname(__file__)
        settings = {
            'root directory': this_dir,
        }
        self.file_scheme_conf.load_settings(settings)
        self.assertEqual(FileSchemeConfiguration.root_directory, this_dir)
