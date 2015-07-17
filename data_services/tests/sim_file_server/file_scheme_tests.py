from .server_tests import FileServerTests
from .test_util import OutputDirMixin
from ...sim_file_server.multi_scheme import MultiSchemeServer
from ...sim_file_server.uri_schemes.file_scheme import FileSchemeConfiguration


class FileSchemeServerTests(FileServerTests, OutputDirMixin):
    """
    Tests for the file server configured for just the "file:" scheme for reading and writing.
    """

    @classmethod
    def setUpClass(cls):
        super(FileSchemeServerTests, cls).setUpClass()

        FileSchemeConfiguration().load_settings({'root directory': cls.get_output_dir()})
        cls.clean_output_dir()

        cls._server = MultiSchemeServer(('file',), 'file')

    def get_server(self):
        return self._server

    def test_data_uri(self):
        """
        Test that the server raises an error with a "data:" URI.
        """
        file_server = self.get_server()
        self.assertRaises(ValueError, file_server.open_for_reading, 'data:,Hello World')
