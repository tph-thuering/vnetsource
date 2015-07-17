from abc import ABCMeta, abstractmethod
import filecmp
import hashlib
import io
import os
import StringIO
import tempfile
import unittest

from ..test_util import DataDirMixin, OpenMalariaData, OutputDirMixin
from ....sim_file_server.util import custom_urlparse


class SchemeHandlerTests(unittest.TestCase, DataDirMixin, OutputDirMixin):
    """
    Base class for tests of a particular URI scheme handler.
    """
    __metaclass__ = ABCMeta

    @classmethod
    def setUpClass(cls):
        super(SchemeHandlerTests, cls).setUpClass()
        cls.contents = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed sit amet vehicula justo.'
        cls.md5_hash = hashlib.md5(cls.contents).hexdigest()

    @abstractmethod
    def get_handler(self):
        """
        Get an instance of the particular server implementation.
        """
        raise NotImplemented()

    def get_file_contents(self, uri_handler, uri):
        """
        Get the contents of a file from a file server
        """
        parsed_url = custom_urlparse(uri)
        with uri_handler.open_in_read_mode(parsed_url) as f:
            contents = f.read()
        return contents

    def test_store_and_get_file(self):
        uri_handler = self.get_handler()
        uri, md5_hash = uri_handler.store_file(self.contents)
        self.assertTrue(uri.startswith(uri_handler.scheme + ':'))
        self.assertEqual(md5_hash, self.md5_hash)

        retrieved_contents = self.get_file_contents(uri_handler, uri)
        self.assertEqual(retrieved_contents, self.contents)

    def test_empty_file(self):
        uri_handler = self.get_handler()
        uri, md5_hash = uri_handler.store_file('')
        self.assertTrue(uri.startswith(uri_handler.scheme + ':'))
        self.assertEqual(md5_hash, hashlib.md5('').hexdigest())

        retrieved_contents = self.get_file_contents(uri_handler, uri)
        self.assertEqual(retrieved_contents, '')

    def test_store_with_string_io_obj(self):
        file_like_obj = StringIO.StringIO(self.contents)
        uri_handler = self.get_handler()
        uri, md5_hash = uri_handler.store_file(file_like_obj)
        self.assertTrue(uri.startswith(uri_handler.scheme + ':'))
        self.assertEqual(md5_hash, self.md5_hash)

        retrieved_contents = self.get_file_contents(uri_handler, uri)
        self.assertEqual(retrieved_contents, self.contents)

    def test_store_with_file_obj(self):
        uri_handler = self.get_handler()
        with tempfile.TemporaryFile() as file_obj:
            #  Put contents into the temporary file
            file_obj.write(self.contents)
            #  Now read the contents from the temporary file, and store them on server
            file_obj.seek(0)
            uri, md5_hash = uri_handler.store_file(file_obj)

        self.assertTrue(uri.startswith(uri_handler.scheme + ':'))
        self.assertEqual(md5_hash, self.md5_hash)

        retrieved_contents = self.get_file_contents(uri_handler, uri)
        self.assertEqual(retrieved_contents, self.contents)

    def test_ctsout_txt_data(self):
        ctsout_txt = OpenMalariaData.CTSOUT_TXT
        uri_handler = self.get_handler()
        uri, md5_hash = uri_handler.store_file(ctsout_txt)
        self.assertTrue(uri.startswith(uri_handler.scheme + ':'))
        self.assertEqual(md5_hash, hashlib.md5(ctsout_txt).hexdigest())

        retrieved_contents = self.get_file_contents(uri_handler, uri)
        self.assertEqual(retrieved_contents, ctsout_txt)

    def test_om_empty_scenario(self):
        empty_scenario = OpenMalariaData.EMPTY_SCENARIO
        uri_handler = self.get_handler()
        uri, md5_hash = uri_handler.store_file(empty_scenario)
        self.assertTrue(uri.startswith(uri_handler.scheme + ':'))
        self.assertEqual(md5_hash, hashlib.md5(empty_scenario).hexdigest())

        retrieved_contents = self.get_file_contents(uri_handler, uri)
        self.assertEqual(retrieved_contents, empty_scenario)

    def test_binary_data(self):
        binary_data = ''.join([chr(i) for i in range(0,256)])
        uri_handler = self.get_handler()
        uri, md5_hash = uri_handler.store_file(binary_data)
        self.assertTrue(uri.startswith(uri_handler.scheme + ':'))
        self.assertEqual(md5_hash, hashlib.md5(binary_data).hexdigest())

        retrieved_contents = self.get_file_contents(uri_handler, uri)
        self.assertEqual(retrieved_contents, binary_data)

    def test_image_file(self):
        image_path = os.path.join(self.get_data_dir(), 'fruit-tree-in-winter-clothing.jpg')
        with io.open(image_path, 'rb') as f:
            computed_md5 = hashlib.md5()
            for chunk in f:
                computed_md5.update(chunk)

        uri_handler = self.get_handler()
        with open(image_path, 'rb') as f:
            uri, md5_hash = uri_handler.store_file(f)
        self.assertTrue(uri.startswith(uri_handler.scheme + ':'))
        self.assertEqual(md5_hash, computed_md5.hexdigest())

        # Assume file is too big to fit into memory, so copy contents from URI into a temporary file
        parsed_url = custom_urlparse(uri)
        with tempfile.NamedTemporaryFile(dir=self.get_output_dir(), delete=False) as temp_file:
            temp_file_path = os.path.join(self.get_output_dir(), temp_file.name)
            with uri_handler.open_in_read_mode(parsed_url) as f:
                for chunk in f:
                    temp_file.write(chunk)
        self.assertTrue(filecmp.cmp(image_path, temp_file_path))
