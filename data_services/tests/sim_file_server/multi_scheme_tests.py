from .server_tests import FileServerTests
from .test_util import OutputDirMixin
from .uri_schemes.https_scheme_tests import TEST_DIR_URL
from ...sim_file_server.multi_scheme import MultiSchemeServer
from ...sim_file_server.uri_schemes.file_scheme import FileSchemeConfiguration
from ...sim_file_server.uri_schemes.https_scheme import HttpsSchemeConfiguration


class MultiSchemeTestsThatWriteDataScheme(FileServerTests, OutputDirMixin):
    """
    Tests for the server when it's configured for multiple URI schemes and for storing new files with "data:" scheme
    """

    @classmethod
    def setUpClass(cls):
        super(MultiSchemeTestsThatWriteDataScheme, cls).setUpClass()

        FileSchemeConfiguration().load_settings({'root directory': cls.get_output_dir()})
        cls.clean_output_dir()

        cls._server = MultiSchemeServer(('data', 'file',), 'data')

    def get_server(self):
        return self._server

    def test_read_file_uri(self):
        """
        Test that the server can read a "file:" URI.
        """
        #  Store a file with the "file:" scheme
        file_scheme_server = MultiSchemeServer(('file',), 'file')
        file_scheme_uri, md5_hash = file_scheme_server.store_file(self.contents)
        self.assertEqual(md5_hash, self.md5_hash)

        #  Now read that URI with the multi-scheme server.
        multi_scheme_server = self.get_server()
        retrieved_contents = self.get_file_contents(multi_scheme_server, file_scheme_uri)
        self.assertEqual(retrieved_contents, self.contents)


class MultiSchemeTestsThatWriteFileScheme(FileServerTests, OutputDirMixin):
    """
    Tests for the server when it's configured for multiple URI schemes and for storing new files with "file:" scheme
    """

    @classmethod
    def setUpClass(cls):
        super(MultiSchemeTestsThatWriteFileScheme, cls).setUpClass()

        FileSchemeConfiguration().load_settings({'root directory': cls.get_output_dir()})
        cls.clean_output_dir()

        cls._server = MultiSchemeServer(('data', 'file',), 'file')

    def get_server(self):
        return self._server

    def test_read_data_uri(self):
        """
        Test that the server can read a "data:" URI.
        """
        #  Store a file with the "data:" scheme
        data_scheme_server = MultiSchemeServer(('data',), 'data')
        data_scheme_uri, md5_hash = data_scheme_server.store_file(self.contents)
        self.assertEqual(md5_hash, self.md5_hash)

        #  Now read that URI with the multi-scheme server.
        multi_scheme_server = self.get_server()
        retrieved_contents = self.get_file_contents(multi_scheme_server, data_scheme_uri)
        self.assertEqual(retrieved_contents, self.contents)


class MultiSchemeTestsThatWriteHttpsScheme(FileServerTests, OutputDirMixin):
    """
    Tests for the server when it's configured for multiple URI schemes and for storing new files with "https:" scheme
    """

    @classmethod
    def setUpClass(cls):
        super(MultiSchemeTestsThatWriteHttpsScheme, cls).setUpClass()

        FileSchemeConfiguration().load_settings({'root directory': cls.get_output_dir()})
        cls.clean_output_dir()
        HttpsSchemeConfiguration().load_settings({'root directory': TEST_DIR_URL})

        cls._server = MultiSchemeServer(('data', 'file', 'https'), 'https')

    def get_server(self):
        return self._server

    def test_read_data_uri(self):
        """
        Test that the server can read a "data:" URI.
        """
        #  Store a file with the "data:" scheme
        data_scheme_server = MultiSchemeServer(('data',), 'data')
        data_scheme_uri, md5_hash = data_scheme_server.store_file(self.contents)
        self.assertEqual(md5_hash, self.md5_hash)

        #  Now read that URI with the multi-scheme server.
        multi_scheme_server = self.get_server()
        retrieved_contents = self.get_file_contents(multi_scheme_server, data_scheme_uri)
        self.assertEqual(retrieved_contents, self.contents)

    def test_read_file_uri(self):
        """
        Test that the server can read a "file:" URI.
        """
        #  Store a file with the "file:" scheme
        file_scheme_server = MultiSchemeServer(('file',), 'file')
        file_scheme_uri, md5_hash = file_scheme_server.store_file(self.contents)
        self.assertEqual(md5_hash, self.md5_hash)

        #  Now read that URI with the multi-scheme server.
        multi_scheme_server = self.get_server()
        retrieved_contents = self.get_file_contents(multi_scheme_server, file_scheme_uri)
        self.assertEqual(retrieved_contents, self.contents)
