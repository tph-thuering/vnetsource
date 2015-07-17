from abc import ABCMeta, abstractmethod
import hashlib
import StringIO
import tempfile
import unittest


class FileServerTests(unittest.TestCase):
    """
    Base class for tests of a particular configuration of a file server.
    """
    __metaclass__ = ABCMeta

    @classmethod
    def setUpClass(cls):
        cls.contents = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet vehicula justo.'
        cls.md5_hash = hashlib.md5(cls.contents).hexdigest()

    @abstractmethod
    def get_server(self):
        """
        Get an instance of the particular server implementation.
        """
        raise NotImplemented()

    def get_file_contents(self, file_server, uri):
        """
        Get the contents of a file from a file server
        """
        with file_server.open_for_reading(uri) as f:
            contents = f.read()
        return contents

    def test_store_and_get_file(self):
        file_server = self.get_server()
        uri, md5_hash = file_server.store_file(self.contents)
        self.assertTrue(uri.startswith(file_server.write_scheme + ':'))
        self.assertEqual(md5_hash, self.md5_hash)

        retrieved_contents = self.get_file_contents(file_server, uri)
        self.assertEqual(retrieved_contents, self.contents)

    def test_empty_file(self):
        file_server = self.get_server()
        uri, md5_hash = file_server.store_file('')
        self.assertTrue(uri.startswith(file_server.write_scheme + ':'))
        self.assertEqual(md5_hash, hashlib.md5('').hexdigest())

        retrieved_contents = self.get_file_contents(file_server, uri)
        self.assertEqual(retrieved_contents, '')

    def test_store_with_string_io_obj(self):
        file_like_obj = StringIO.StringIO(self.contents)
        file_server = self.get_server()
        uri, md5_hash = file_server.store_file(file_like_obj)
        self.assertTrue(uri.startswith(file_server.write_scheme + ':'))
        self.assertEqual(md5_hash, self.md5_hash)

        retrieved_contents = self.get_file_contents(file_server, uri)
        self.assertEqual(retrieved_contents, self.contents)

    def test_store_with_file_obj(self):
        file_server = self.get_server()
        with tempfile.TemporaryFile() as file_obj:
            #  Put contents into the temporary file
            file_obj.write(self.contents)
            #  Now read the contents from the temporary file, and store them on server
            file_obj.seek(0)
            uri, md5_hash = file_server.store_file(file_obj)

        self.assertTrue(uri.startswith(file_server.write_scheme + ':'))
        self.assertEqual(md5_hash, self.md5_hash)

        retrieved_contents = self.get_file_contents(file_server, uri)
        self.assertEqual(retrieved_contents, self.contents)

    def test_bad_uri(self):
        file_server = self.get_server()
        self.assertRaises(ValueError, file_server.open_for_reading, 'bad:foo bar')
