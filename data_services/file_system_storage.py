import os
from StringIO import StringIO


def save_to_system(file_object):
    """
    This method is used to save files to the system.
    :param File file_object: The file to save to the filesystem.
    :rtype: - A tuple containing a boolean success flag and a message. If success is True, the message is the path to
            the file. If success is False then the message is the exception.
    """
    output_directory = 'output_zip_files'
    path = os.path.join(os.path.abspath(os.path.dirname(__file__)), output_directory)
    path_with_filename = os.path.join(path, str(file_object.name))

    try:
        with open(path_with_filename, 'wb') as tmp_file:
            file_object.open()
            tmp_file.write(file_object.read())
            file_object.close()
        return True, path_with_filename
    except EnvironmentError as e:
        return False, str(e)


class NamedStringIO(StringIO):
    """
    This class provides a name attribute to the StringIO.StringIO class.
    To Be implemented: - Unit tests that test the functionality of the cStringIo object to ensure the wrapper works as
                         expected.
    """
    def __init__(self, name, message):
        """
        Custom initialization method.
        :param str name: The filename.
        :return: Null
        """
        self.name = name
        StringIO.__init__(self, message)

    def open(self):
        pass