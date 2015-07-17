########################################################################################################################
# VECNet CI - Prototype
# Date: 05/02/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
########################################################################################################################

import os
import zipfile
import shutil
import uuid
import tempfile
import shutil
from data_services.models import DimExecution
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from abc import ABCMeta


class Base_ingester(object):
    """This is the base_ingester class for ingesters into the datawarehouse.  All ingesters
    should inherit from this class.  The reason is for future maintainability and added
    flexibility of being able to run any ingester anonymously.
    """

    __metaclass__ = ABCMeta



    def __init__(self, base_path=None):
        """
        This is the base init, this sets model agnostic parameters for ingestion.  This was meant to be
        called by the ingesters to set these parameters.

        An optional parameter can be passed in (called base_path) that will set the temporary path parent.

        The current list of parameters it sets are below:

        =================  =============
        Parameter          Use
        =================  =============
        FILES_OF_INTEREST This is used to determine which files to unpack during the ingestion process
        temporary_path    Location of temporary folder where files to be ingested are unpacked to
        =================  =============


        :param base_path: Parent folder of where files will be unpacked to
        :type base_path: str
        """
        #: Used to store list of files to be ingested, key structure left up to daughter class
        self.FileList = None

        #: Run instance that the particular files are related to
        self.run = None

        #: Execution instance that the particular files are related to
        self.execution = None

        #: Replication of the instance the files are to be ingested against
        self.replication = None

        ## base path for file extraction
        self.BASE_PATH = None

        ## temporary path that houses files during processing
        self.temporary_path = None

        self.FILES_OF_INTEREST = tuple()

        if base_path is not None and not isinstance(base_path, (str, unicode)):
            raise TypeError("tmp_parent must be a string or unicode, found %s" % type(base_path))


        self.BASE_PATH = (base_path if base_path is not None else tempfile.gettempdir())

        # Check if the temporary parent is writeable
        if not os.access(self.BASE_PATH, os.W_OK):
            raise ValueError("Temporary parent '%s' is not writeable" % base_path)

        self.temporary_path = self.BASE_PATH + os.path.sep + str(uuid.uuid4())

        # Now we make the temporary directory and check to make sure the temporary path is writeable
        try:
            os.mkdir(self.temporary_path)
        except OSError:
            raise OSError("Temporary path '%s' already exists" % self.temporary_path)

        if not os.access(self.temporary_path, os.W_OK):
            raise ValueError("Temporary path '%s' is not writeable" % os.path.dirname(self.temporary_path))

    # def __del__(self):
    #     """
    #     This is the exit method and will cleanup temporary files, even if there is an exception.  This will walk the
    #     tree of the temporary path, deleting all files and folders therein, and then removing the temporary directory
    #     itself.
    #     """
    #     if self.temporary_path:
    #         self._cleanupIngester()

    def _cleanupIngester(self):
        """
        This method will clean the ingestion files up, deleting the appropriate directory and files within.  This should
        always be called when the object is destroyed.  This is why it is called from __del__.

        The reason this exists as its own method is to make sure that in command line utilities things are cleaned up as
        there is no gaurantee that __del__ is run when something exits the interpreter.
        """
        shutil.rmtree(self.temporary_path)
        os.rmdir(self.temporary_path)

    ## This is the unicode function
    #
    # This will return some information about the execution that this is being
    # ingested into
    def __unicode__(self):
        return self.execution.name

    ## This is the ingest method

    # This is where the all files will be ingested into the datawarehouse.  This code
    # is usually a loop over file names or calls to different parser methods.  It should
    # take no arguments and completely ingest the file
    def ingest(self):
        """
        This method is responsible for calling the parse_file methods.  This can be a factory type setup, or
        an if-then-elif structure.  This should completely ingest the file.
        """
        pass

    ## This is the parse_file method
    #
    # This is a method which will ingest a single file.  This can be given a file name, id,
    # or whatever the author of the ingester needs.  There is an option, in the future, to
    # make sure that all "parse_file" methods point here can ingest different files based on
    # arguments.  This could be helpful future functionality, but for now we leave it alone.
    # Kwargs is added here to allow for arguments to be passed
    def parse_file(self, **kwargs):
        """
        This method is an abstract method that should be overridden.  This is where the parsing code for
        any given file type should go.  If you have more than one file type.  Than many 'parsing' methods
        can be created and called from ingest.
        """
        pass

    def unpack_files(self, zip_file):
        """
        This method extracts a zipfile onto the file system and sets up the filedict to contain the paths of the
        extracted files.  Filedict is then used by other methods of the ingester to ingest the extracted files.
        :param str zip_file: A string containing the path to a file on the system.
        """
        filedict = {}
        path = self.temporary_path
        if zipfile.is_zipfile(zip_file):
            z = zipfile.ZipFile(zip_file, "r")
            fileList = [f.filename for f in z.filelist]
        else:
            raise TypeError("%s is not a valid zipfile" % zip_file)

        for f in fileList:
            for name in self.FILES_OF_INTEREST:
                if name in f:
                    print "UNPACKING", f
                    z.extract(f, path)
                    filedict[name] = str(path + os.path.sep + f)

        return filedict

    def save_to_system(self, zip_files):
        """
        This method is used to save files to the system.

        :param FileObject zip_files: The file to save to the filesystem.
        :rtype: - The path the file was saved to including the filename if the save was successful.
                - False if the save was not successful.
        """
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'output_zip_files')
        fs = FileSystemStorage(location=path)
        try:
            fs.save(zip_files.name, ContentFile(zip_files.read()))
            return fs.path(zip_files.name)
        except IOError:
            return False

    def set_status(self, status_id, status_msg=''):
        """
        This method is responsible for setting the status of a given replication.  If no status message is given, then
        this method assumes that the status method should be null, and therefore sets the model field to None.

        :param status_id: Integer status id
        :type status_id: int
        :param status_msg: Message to be saved, if any
        :type status_msg: str or unicode
        """
        if not isinstance(status_id, int):
            return ValueError('Status_id must be an integer, received %s', type(status_id))
        if not isinstance(status_msg, (str, unicode)):
            return ValueError('Status_msg must be a string or unicode, received %s' % type(status_msg))

        self.replication.status = status_id
        if status_msg is not '':
            self.replication.status_text = status_msg
        else:
            self.replication.status_text = None

        self.replication.save()
