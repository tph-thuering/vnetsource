from .server_tests import FileServerTests
from ...sim_file_server.multi_scheme import MultiSchemeServer


class DataSchemeServerTests(FileServerTests):
    """
    Tests for the file server configured for just the "data:" scheme for reading and writing.
    """

    @classmethod
    def setUpClass(cls):
        super(DataSchemeServerTests, cls).setUpClass()
        cls._server = MultiSchemeServer(('data',), 'data')

    def get_server(self):
        return self._server

    def test_file_uri(self):
        """
        Test that the server raises an error with a "file:" URI.
        """
        file_server = self.get_server()
        self.assertRaises(ValueError, file_server.open_for_reading, 'file://foo/bar.txt')
