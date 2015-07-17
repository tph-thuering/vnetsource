"""
This contains the EMOD specific baseline class, inherited from the Baseline class
"""
from vecnet.emod.demographics import decompile_demographics

from baseline import Baseline
from data_services.models import DimModel


class EMODBaseline(Baseline):
    """
    This is the EMOD specific scenario where required files is set appropriately and specific file getters/setters
    exist to make it convenient.
    """

    def __init__(self, **kwargs):
        """
        Here we set the required file types
        """
        super(EMODBaseline, self).__init__(**kwargs)

        self.required_filetypes = [
            'air binary',
            'air json',
            'humidity binary',
            'humidity json',
            'land_temp binary',
            'land_temp json',
            'rainfall binary',
            'rainfall json',
            'config',
            'campaign',
            'demographics',
        ]
        """The required files for a single node simulation"""

        if self.model is not None:
            if isinstance(self.model, DimModel):
                if self.model.model != 'EMOD':
                    raise ValueError("EMODBaseline can only be used with EMOD Models")
        else:
            qs = DimModel.objects.filter(model='EMOD')
            self.model = qs[0]

    def get_air_file(self, binfile=False, jsonfile=False):
        """
        This will get the weather file type

        :param binfile: Boolean expressing whether the binfile should be returned or not (Default False)
        :type binfile: bool
        :param jsonfile: Boolean expressing whether the jsonfile should be returned or not (Default False)
        :type jsonfile: bool
        :returns: DimBinFile instance (or tuple of instances if both jsonfile and binfile are True)
        :raises: ValueError is both binfile and jsonfile are False
        """
        if not binfile and not jsonfile:
            raise ValueError("Both jsonfile and binfile were false, at least one must be true")
        try:
            return self._get_file_by_subject('air', binfile, jsonfile)
        except:
            raise

    def get_humidity_file(self, binfile=False, jsonfile=False):
        """
        This will get the humidity binfile or json file, pending on the boolean inputs

        :param binfile: Boolean expressing whether the binfile should be returned or not (Default False)
        :type binfile: bool
        :param jsonfile: Boolean expressing whether the jsonfile should be returned or not (Default False)
        :type jsonfile: bool
        :returns: DimBinFile instance (or tuple of instances if both jsonfile and binfile are True)
        :raises: ValueError is both binfile and jsonfile are False
        """
        if not binfile and not jsonfile:
            raise ValueError("Both jsonfile and binfile were false, at least one must be true")
        try:
            return self._get_file_by_subject('humidity', binfile, jsonfile)
        except:
            raise
    
    def get_land_temp_file(self, binfile=False, jsonfile=False):
        """
        This will get the weather file type

        :param binfile: Boolean expressing whether the binfile should be returned or not (Default False)
        :type binfile: bool
        :param jsonfile: Boolean expressing whether the jsonfile should be returned or not (Default False)
        :type jsonfile: bool
        :returns: DimBinFile instance (or tuple of instances if both jsonfile and binfile are True)
        :raises: ValueError is both binfile and jsonfile are False
        """
        if not binfile and not jsonfile:
            raise ValueError("Both jsonfile and binfile were false, at least one must be true")
        try:
            return self._get_file_by_subject('land_temp', binfile, jsonfile)
        except:
            raise
    
    def get_rainfall_file(self, binfile=False, jsonfile=False):
        """
        This will get the weather file type

        :param binfile: Boolean expressing whether the binfile should be returned or not (Default False)
        :type binfile: bool
        :param jsonfile: Boolean expressing whether the jsonfile should be returned or not (Default False)
        :type jsonfile: bool
        :returns: DimBinFile instance (or tuple of instances if both jsonfile and binfile are True)
        :raises: ValueError is both binfile and jsonfile are False, ObjectDoesNotExist if no file has been saved or
                if the scenario hasn't been saved
        """
        if not binfile and not jsonfile:
            raise ValueError("Both jsonfile and binfile were false, at least one must be true")
        try:
            return self._get_file_by_subject('rainfall', binfile, jsonfile)
        except:
            raise
    
    def get_config_file(self):
        """
        This will get the configuration file
        
        :returns: DimBinFile object or Queryset of objects if more than one configuration file is returned
        :raises: ValueError is both binfile and jsonfile are False, ObjectDoesNotExist if no file has been saved or
                if the scenario hasn't been saved
        """
        try:
            return self.get_file_by_type('config')
        except:
            raise
    
    def get_campaign_file(self):
        """
        This will get the campaign file 
        
        :returns: DimBinFile object or Queryset of objects if more than one campaign file is returned
        :raises: ValueError is both binfile and jsonfile are False, ObjectDoesNotExist if no file has been saved or
                if the scenario hasn't been saved
        """
        try:
            return self.get_file_by_type('campaign')
        except:
            raise

    def get_demographics_file(self):
        """
        This will get the campaign file
        :returns: DimBinFile object or Queryset of objects if more than one demographics file is returned
        :raises: ValueError is both binfile and jsonfile are False, ObjectDoesNotExist if no file has been saved or
                if the scenario hasn't been saved
        """
        return self.get_file_by_type('demographics')

    def get_uncompiled_demographics_file(self):
        uncompiled_demographics = decompile_demographics(self.get_demographics_file().content, True)
        print uncompiled_demographics
        return uncompiled_demographics
        # return self.get_demographics_file().content

    def _get_file_by_subject(self, fsub, binfile=False, jsonfile=False):
        """
        This will fetch the files by type, and grab the appropriate bin or json file.  This is to keep from
        repeating the same if/then/else structure in each particular file type

        :param fsub: Subject of the file ('air', 'land_temp', 'humidity', 'rainfall') are supported by EMOD
        :type fsub: str
        :param binfile: Determines whether to return the binary file
        :type binfile: bool
        :param jsonfile: Determines whether to return the json file
        :type jsonfile: bool
        :returns: DimBinFile instance(s)
        :raises: ValueError is both binfile and jsonfile are False, ObjectDoesNotExist if no file has been saved or
                if the scenario hasn't been saved
        """
        if binfile and jsonfile:
            binfile = self.get_file_by_type('%s binary' % fsub)
            jsonfile = self.get_file_by_type('%s json' % fsub)
            return jsonfile, binfile
        elif binfile:
            return self.get_file_by_type('%s binary' % fsub)
        elif jsonfile:
            return self.get_file_by_type('%s json' % fsub)
        else:
            raise ValueError("Both jsonfile and binfile were false, at least one must be true")

    def _add_file_by_subject(self, fsub, path, description=None, name=None, jsonfile=False):
        """
        This will add files by subject.  'Subject' here is a broad term, meaning a set of files.  Each of these sets
        of files will have a binfile and json file.  The boolean jsonfile (default False) determines whether this is a
        json file or binfile.  Only one file can be added this way at a time.
        
        :param fsub:  The subject of the file to be added (air, land_temp, humidity, etc)
        :type fsub: str
        :param path: The path to the file to be uploaded
        :type path: str 
        :param description: (Optional) A description of this file.  To be saved in the DW and used in the UI
        :type description: str
        :param name: (Optional) The name of the file.  If left blank, the filename in the path will be used as the name 
        :type name: str
        :param jsonfile: Determines whether you are adding a JSON file or a BinFile (Defaults False, which is Binfile)
        :type jsonfile: bool
        :returns: A boolean, true if the file was added, false otherwise
        """
        if jsonfile:
            type_str = '%s json' % fsub
        else:
            type_str = '%s binary' % fsub
        
        return self.add_file(type_str, path, description, name)
        
    def add_land_temp_file(self, path, description=None, name=None, jsonfile=False):
        """
        Adds the land temperature json or binary file.  The flasg is_json, default to false, determines if it is the
        JSON file being added or if False, the binary file being added
        
        :param path: Path to the file to be attached to this object
        :type path: str 
        :param description: (Optional) Description of the file 
        :type description: str 
        :param name: (Optional) Name of the file.  If left blank, the filename in the path will be used as the name
        :type name: str 
        :param jsonfile: Determines whether you are adding a JSON file or a BinFile (Defaults False, which is BinFile)
        :type jsonfile: bool
        :returns: A boolean, true if the file was added, false otherwise
        :raises: ValueError if no file was found or if no name could be derived, or the file was 0 size.
        """
        try:
            return self._add_file_by_subject('land_temp', path, description, name, jsonfile)
        except:
            raise
    
    def add_air_file(self, path, description=None, name=None, jsonfile=False):
        """
        Adds the land temperature json or binary file.  The flasg is_json, default to false, determines if it is the
        JSON file being added or if False, the binary file being added

        :param path: Path to the file to be attached to this object
        :type path: str
        :param description: (Optional) Description of the file
        :type description: str
        :param name: (Optional) Name of the file.  If left blank, the filename in the path will be used as the name
        :type name: str
        :param jsonfile: Determines whether you are adding a JSON file or a BinFile (Defaults False, which is BinFile)
        :type jsonfile: bool
        :returns: A boolean, true if the file was added, false otherwise
        :raises: ValueError if no file was found or if no name could be derived, or the file was 0 size.
        """
        try:
            return self._add_file_by_subject('air', path, description, name, jsonfile)
        except:
            raise

    def add_humidity_file(self, path, description=None, name=None, jsonfile=False):
        """
        Adds the land temperature json or binary file.  The flasg is_json, default to false, determines if it is the
        JSON file being added or if False, the binary file being added

        :param path: Path to the file to be attached to this object
        :type path: str
        :param description: (Optional) Description of the file
        :type description: str
        :param name: (Optional) Name of the file.  If left blank, the filename in the path will be used as the name
        :type name: str
        :param jsonfile: Determines whether you are adding a JSON file or a BinFile (Defaults False, which is BinFile)
        :type jsonfile: bool
        :returns: A boolean, true if the file was added, false otherwise
        :raises: ValueError if no file was found or if no name could be derived, or the file was 0 size.
        """
        try:
            return self._add_file_by_subject('humidity', path, description, name, jsonfile)
        except:
            raise

    def add_rainfall_file(self, path, description=None, name=None, jsonfile=False):
        """
        Adds the land temperature json or binary file.  The flasg is_json, default to false, determines if it is the
        JSON file being added or if False, the binary file being added

        :param path: Path to the file to be attached to this object
        :type path: str
        :param description: (Optional) Description of the file
        :type description: str
        :param name: (Optional) Name of the file.  If left blank, the filename in the path will be used as the name
        :type name: str
        :param jsonfile: Determines whether you are adding a JSON file or a BinFile (Defaults False, which is BinFile)
        :type jsonfile: bool
        :returns: A boolean, true if the file was added, false otherwise
        :raises: ValueError if no file was found or if no name could be derived, or the file was 0 size.
        """
        try:
            return self._add_file_by_subject('rainfall', path, description, name, jsonfile)
        except:
            raise

    def add_config_file(self, path, description=None, name=None):
        """
        This will attach the above config file to the scenario

        :param path: Path to the file to be attached to this object
        :type path: str
        :param description: (Optional) Description of the file
        :type description: str
        :param name: (Optional) Name of the file.  If left blank, the filename in the path will be used as the name
        :type name: str
        :returns: A boolean, true if the file was added, false otherwise
        :raises: ValueError if no file was found or if no name could be derived, or the file was 0 size.
        """
        try:
            return self.add_file('config', path, description, name)
        except:
            raise

    def add_campaign_file(self, path, description=None, name=None):
        """
        This will attach the above config file to the scenario

        :param path: Path to the file to be attached to this object
        :type path: str
        :param description: (Optional) Description of the file
        :type description: str
        :param name: (Optional) Name of the file.  If left blank, the filename in the path will be used as the name
        :type name: str
        :returns: A boolean, true if the file was added, false otherwise
        :raises: ValueError if no file was found or if no name could be derived, or the file was 0 size.
        """
        try:
            return self.add_file('campaign', path, description, name)
        except:
            raise

    def add_demographics_file(self, path, description=None, name=None):
        """
        This will attach the above config file to the scenario

        :param path: Path to the file to be attached to this object
        :type path: str
        :param description: (Optional) Description of the file
        :type description: str
        :param name: (Optional) Name of the file.  If left blank, the filename in the path will be used as the name
        :type name: str
        :returns: A boolean, true if the file was added, false otherwise
        :raises: ValueError if no file was found or if no name could be derived, or the file was 0 size.
        """
        try:
            return self.add_file('demographics', path, description, name)
        except:
            raise

    def save(self, **kwargs):
        """
        Here we put EMOD specific validation in when this basline is saved.

        :returns: Tuple containing DW Baseline ID, completeness of scenario
        :raises: ValueError if model or user objects aren't specified, or if the model isn't EMOD or a DimModel instance
        """
        if not isinstance(self.model, DimModel):
            raise ValueError("model Must be a saved DimModel instance")
        else:
            if self.model.model != 'EMOD':
                raise ValueError("EMODBaseline can only operate on EMOD Baselines.  Expected model EMOD, found %s"
                                 % self.model.model)
        try:
            return super(EMODBaseline, self).save(**kwargs)
        except:
            raise