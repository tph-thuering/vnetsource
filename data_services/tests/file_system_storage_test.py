from django.test import TestCase
from data_services.file_system_storage import save_to_system, NamedStringIO


class FileSystemStorageTest(TestCase):

    def test_save_to_system(self):
        """
        Tests that the save_to_system method saves a file to the system, returns a path, and that the saved file
        contains the same contents as the original file.
        :return: Null
        """
        TMP_STRING = "Message content here."
        # create a file-like object and call save_to_system on it
        tmp_file = NamedStringIO("test.py", TMP_STRING)
        success, path = save_to_system(tmp_file)
        # check that a valid path was returned, ensure the path is a string or unicode, and make sure the contents
        # of the written file match the contents of the file-like object
        self.assertTrue(success)
        self.assertTrue(isinstance(path, (str, unicode)))
        with open(path, 'rb') as tmp_file_2:
            self.assertEqual(TMP_STRING, tmp_file_2.read())