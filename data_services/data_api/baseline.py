"""
This module describes the baseline and how to complete a baseline.  A baseline is a fully configured set of inputs
for models.  With a baseline, a model will run without error to completion.  Currently, two sets of baselines are
allowed in VecNet, Open Malaria and EMOD.  Below is a table describing the files required for each:
============    ===================
model           File list (format)
============    ===================
EMOD            Demographics (Binary/JSON), weather (Binary/JSON), campaign (JSON), config (JSON)
Open Malaria    Input (XML)
============    ===================


The Baseline class is an Abstract base class with a factory Class method.  The EMOD_Basline and Open_Malaria_Baseline
are the two concrete classes for the table above.
"""

import os
import datetime
import hashlib
from abc import ABCMeta
from data_services.models import DimBinFiles, DimBaseline, DimModel, DimUser, DimLocation, DimTemplate
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.utils import timezone

class Baseline(object):
    """
    This is an abstract base class defining Baselines.  Through this basic interface files can be added to a scenario,
    model specific baselines can be instantiated, and baselines can be checked.  This *CANNOT* be instantiated itself
    """

    __metaclass__ = ABCMeta

    def __init__(self, name=None, description=None, user=None, model=None):
        """
        This will initialize the class specific variables.
        """
        if user is not None:
            if isinstance(user, DimUser):
                if not user.pk:
                    raise ValueError("user Must be a saved DimUser instance")
            else:
                raise ValueError("user Must be a DimUser instance")

        if model is not None:
            if isinstance(model, DimModel):
                if not model.pk:
                    raise ValueError("model Must be a saved DimModel instance")
            else:
                raise ValueError("model Must be a DimModel instance")

        self.files = list()
        """A list of dictionaries of files to be added"""

        self.required_filetypes = list()
        """This is a list of all required filetypes needed for a 'complete' scenario"""

        self.dimbaseline = None
        """This is the data warehouse object for this scenario"""

        self.id = None
        """DimBaseline id, after it is saved"""

        self._name = name
        """Name of the scenario"""

        self._description = description
        """Description of the scenario, useful for UI hints"""

        self._is_approved = None
        """Whether the scenario has been approved"""

        self.version = None
        """Last saved time and version number"""

        self._is_public = None
        """Whether the scenario is public"""

        self._is_deleted = None
        """Whether the scenario is deleted"""

        self._last_edited = None
        """The last time this scenario was edited"""

        self._is_completed = None
        """Boolean describing the completed status of the Baseline (if it has all required files)"""

        self.location = None
        """DimLocation instance"""

        self.template = None
        """DimTemplate instance"""

        self.model = model
        """DimModel instance or string/unicode of the model this scenario is purposed for"""

        self.model_version = None
        """string/unicode of the model_version this scenario is purposed for"""

        self.user = user
        """DimUser instance specifying owner of the scenario"""

        return

    @property
    def has_required_files(self):
        """
        This will check to see if the scenario is complete.  If it is, it will check to make sure that the _is_complete
        token is set to true.  If it is not, this will update the dimbaseline object.
        """
        if self.dimbaseline is None:
            return False
        #
        #def _eval_files(f):
        #    if f['id'] is None and f['hash'] is None:
        #        return False
        #    else:
        #        return f['type'] in self.required_filetypes

        types = map(lambda x: x['type'], self.files)
        complete = all(map(lambda x: x in types, self.required_filetypes))
        #complete = all(map(_eval_files, self.files))

        if complete and self._is_completed:
            return True
        elif complete and not self._is_completed:
            self.dimbaseline.is_completed = True
            self._is_completed = True
            return True
        else:
            return False

    @property
    def is_approved(self):
        """
        This will return the approval status of this particular scenario.  If the scenario is not complete, it cannot
        be approved.
        """
        return self.has_required_files and self._is_approved

    @is_approved.setter
    def is_approved(self, status):
        """
        This will set the approval status of the scenario.

        As per Alex Vyushkov there is purposely little logic here as this is determined by the UI team

        :param status: Boolean describing the status of the scenario
        :type status: bool
        :raises: ValueError if the scenario is incomplete, or if the scenario has not been saved (or is not from the
                datawarehouse)
                 TypeError if anything except a bool is passed in
        """
        if self.dimbaseline is None:
            raise ValueError("Approval can only be set once a scenario has been saved")

        if not isinstance(status, bool):
            raise TypeError("Parameter status must be a boolean, received %s" % type(status))

        if not self.has_required_files and status:
            raise ValueError("Baseline is not complete, and cannot be approved")

        self.dimbaseline.is_approved = True
        self.dimbaseline.save()
        self._is_approved = status

    @property
    def is_deleted(self):
        """
        Thie is the is_deleted property.  It will return a boolean stating whether this scenario has been
        deleted or not.

        :returns: Boolean about whether scenario has been deleted
        :raises: ValueError if Baseline has not been saved to data warehouse
        """
        if self.id is None:
            raise ValueError("is_deleted can only be checked on saved baselines")

        return self._is_deleted

    @is_deleted.setter
    def is_deleted(self, opt):
        """
        This will set the is_deleted flag.

        :param opt: Boolean you want to set is_deleted to
        :type opt: bool
        :returns: Boolean representing the current is_deleted state
        :raises: ValueError if Baseline has not been saved to data warehouse or if opt is not a boolean
                 Any Exception raised by Django model save
        """
        if self.id is None:
            raise ValueError("is_deleted can only be checked on saved baselines")
        if not isinstance(opt, bool):
            raise ValueError("is_deleted can only be set true or false")

        try:
            self._is_deleted = opt
            self.dimbaseline.is_deleted = opt
            self.dimbaseline.save()
        except:
            raise

    @property
    def name(self):
        """
        This grabs the _name property of the Baseline object
        """
        return self._name

    @name.setter
    def name(self, sname):
        """
        This checks to make sure that the name being passed in is a string, if it is, then it will check to see if
        the Baseline has been saved.  If it has been saved, it will save after setting the scenario.
        """
        if not isinstance(sname, (str, unicode)):
            raise TypeError("Name must be a string, received %s" % type(sname))

        if self.dimbaseline is not None:
            self._name = sname
            self.dimbaseline.name = sname
            self.dimbaseline.save()
        else:
            self._name = sname

    @property
    def is_saved(self):
        """
        This returns whether a data warehouse object is backing this particular scenario instance.  If you create
        a new instance of scenario, it will not be saved.  Once you elicit a save() from this scenario, a data
        warehouse object corresponding to this scenario will be created.

        Currently, if you instantiate from the datawarehouse, this will report as saved.  Future functionality may
        change this.
        """
        return self.dimbaseline is not None and isinstance(self.dimbaseline, DimBaseline)

    @property
    def description(self):
        """
        This is a getter for description
        """
        return self._description

    @description.setter
    def description(self, desc):
        """
        This sets the description and updates the dimbaseline object if this Baseline has one.
        """
        if not isinstance(desc, (str, unicode)):
            raise TypeError("Description must be a string, received" % type(desc))
        if self.is_saved:
            self.dimbaseline.description = desc
            self.dimbaseline.save()
        self._description = desc
        return

    def delete(self):
        """
        This is the "soft" delete for the Baseline object.  The same effect can be achieved through using the
        is_deleted setter.

        :returns: True if deleted, false otherwise
        :raises: ValueError if Baseline has not been saved to data warehouse or if opt is not a boolean
                 Any Exception raised by Django model save
        """
        self.is_deleted = True
        return not self.is_deleted and not self.dimbaseline.is_deleted

    @classmethod
    def list_baselines(cls, user, with_public=True, with_deleted=False, **kwargs):
        """
        This will fetch the baselines currently in the data warehouse and pull them out as a list of dictionaries.

        We allow any keywords acceptable in a DimBaseline.objects.filter, however, for security we replace the user
        keyword.

        :param user: DimUser instance that narrows search results to dim_user
        :type user: DimUser
        :param is_public: Whether to include public baselines or not
        :type is_public: bool
        :param kwargs: Any Keyword arguments a DimBaseline object would take for searching
        """
        if not isinstance(user, DimUser):
            raise ValueError("user Must be a saved DimUser instance")

        if not kwargs:
            kwargs = {
                'user': user,
            }

        if with_deleted and 'is_deleted' in kwargs:
            kwargs.pop('is_deleted', None)
        else:
            kwargs['is_deleted'] = with_deleted
        # TODO: Design public system
        # if with_public and 'public' in kwargs:
        #     kwargs.pop('is_public', None)
        # else:
        #     kwargs['is_public'] = with_public
        if 'user' in kwargs:
            kwargs['user'] = user

        # exclude(name="") is added as a workaround to Bug #6410
        # https://redmine.crc.nd.edu/redmine/issues/6410
        # This should be reverted back after Task #6411 (New Workflow - Separate out the Step 1 "Location"
        # into a standalone view) is completed
        # https://redmine.crc.nd.edu/redmine/issues/6411
        baselines = DimBaseline.objects.filter(**kwargs).exclude(name="").values(
            'id',
            'name',
            'description',
            'last_modified',
            'model',
            'model_version',
            'location',
            'template',
            'is_completed',
            'is_approved'
        )

        return list(baselines)

    @classmethod
    def from_dw(cls, **kwargs):
        """
        This will fetch and create a scenario object from the data warehouse.  The search parameters are
        the same as the DimBaseline object's filter method.  All will be accepted, however, if multiple
        objects are returned and are of different baselines (as in not the same scenario but different
        versions), an exception will be thrown.

        If no scenario is created, then an ObjectDoesNotExist exception will be raised.

        :param kwargs: Keyword arguments that can be fed into DimBasline's filter method
        :raises: ObjectDoesNotExist, MultipleObjectsReturned
        :returns: Baseline
        """
        qs = DimBaseline.objects.filter(**kwargs)

        if not qs.exists():
            raise ObjectDoesNotExist("No object with parameters %s were found" % str(kwargs))
        elif len(qs) > 1:
            names = list()
            models = list()
            model_versions = list()
            locations = list()
            templates = list()
            baseline_max = qs[0]
            bobj = None
            for bline in qs:
                names.append(bline.name)
                locations.append(bline.location)
                models.append(bline.model)
                model_versions.append(bline.model_version)
                if bline.last_modified > baseline_max.last_modified:
                    bobj = bline
            if len(set(names)) == 1 and len(set(models)) == 1 and len(set(locations)) == 1:
                baseline = cls()
                if bobj is None:
                    raise MultipleObjectsReturned("More than one scenario was returned for parameters %s" % str(kwargs))
                baseline.dimbaseline = bobj
            else:
                raise MultipleObjectsReturned("More than one scenario was returned for parameters %s" % str(kwargs))
        else:
            baseline = cls()
            baseline.dimbaseline = qs[0]
        baseline._update()
        return baseline

    @classmethod
    def from_files(cls, files, name=None, description=None, user=None, model=None):
        """
        This will create a scenario from a set of files.

        *THIS WILL NOT SAVE THE BASELINE TO THE DATA WAREHOUSE*

        :param files: List of dictionaries describing files.  Each dictionary should have file_type, path, description,
                name keys, where name and description are optional.
        :type files: list
        :returns Baseline
        """
        if user is not None and not isinstance(user, DimUser):
            raise ValueError("user Must be an instance of DimUser")
        if model is not None and not isinstance(model, DimModel):
            raise ValueError("model Must be an instance of DimModel")

        baseline = cls(name=name, description=description, user=user, model=model)
        for f in files:
            baseline.add_file(**f)
        return baseline

    def add_file(self, file_type, path, description=None, name=None):
        """
        This will add a file of a certain type to a scenario.

        *If a file type has already been added, this will be overridden!*

        If no name is given, the last value in the path will be used as a filename.  For instance,

        .. code-block::
            file_path = '/path/to/scenario/weather/binaryfile/weather.bin   // If name is None, name='weather.bin'

        This will save to the DimBaseline object immediately, creating new versions of the object if it is complete
        and approved.

        :param file_type: Type of file
        :type file_type: str
        :param path: Fully qualified path to file
        :type path: str
        :param description: Description of the file
        :type description: str
        :param name: File name to be saved (and used in where necessary in baselines)
        :type name: str
        :raises: ValueError if no file was found or if no name could be derived, or the file was 0 size.
        :returns: A boolean, true if the file was added, false otherwise
        """
        if not os.path.isfile(path):
            raise ValueError("No file at path %s was found" % path)

        if os.stat(path).st_size == 0:
            raise ValueError("File %s was found, but is size 0" % path)

        # exists = filter(lambda file_dic: file_dic['type'] == file_type, self.files)
        # if len(exists) > 0:
        #     for obj in exists:
        #         self.files.remove(obj)

        if not name:
            name = os.path.basename(path)

        if name == '':
            raise ValueError("Path %s must be a path to a file, no file found at end of path" % path)

        if not self.is_saved:
            self.save()

        fhash, bindata = DimBinFiles.prepare_file(path)

        attached_files = self.dimbaseline.binfiles.filter(
            file_name=name,
            file_hash=fhash,
            file_type=file_type
        ).defer('content')

        if attached_files.exists():
            # The file is already attached to this object
            return True
        else:
            dbf, created = DimBinFiles.objects.get_or_create(
                file_name=name,
                file_hash=fhash,
                file_type=file_type
            )
            if created:
                dbf.content = bindata
                dbf.description = description
                dbf.save()
                return self.add_binfile(dbf)
            else:
                # if self.is_approved and self.has_required_files:
                #     self._new_save_baseline_version()
                #     self._update()
                self.add_binfile(dbf)
                return True

    def add_file_from_string(self, file_type, name, content, description=None):
        """
        Adds a dimbinfile with the contents of the given string.  This save happens immediately

        :param file_type: Type of file to be attached to this scenario
        :type file_type: str
        :param name: Name of the file to be attached
        :type name: str
        :param content: Content of the file to be added
        :type content: str
        :param description: (Optional) Description of the file to be added
        :type description: str
        :raises: ValueError when an empty string is passed or the name is an empty string
        :returns: Boolean, true if the file was added, false otherwise
        """
        if len(name) == 0 or len(content) == 0:
            raise ValueError("Name and content must both be non-empty strings")

        m = hashlib.md5()
        m.update(content)
        shash = m.hexdigest()

        if not self.is_saved:
            self.save()

        attached_files = self.dimbaseline.binfiles.filter(
            file_name=name,
            file_hash=shash,
            file_type=file_type
        ).defer('content')

        if attached_files.exists():
            # The file is already attached to this object
            return True
        else:
            dbf, created = DimBinFiles.objects.get_or_create(
                file_name=name,
                file_hash=shash,
                file_type=file_type
            )
            if created:
                dbf.content = content
                dbf.description = description
                dbf.save()
                return self.add_binfile(dbf)
            else:
                # if self.is_approved and self.has_required_files:
                #     self._new_save_baseline_version()
                #     self._update()
                self.add_binfile(dbf)
                return True

    def add_binfile(self, dbf):
        """
        This will add a saved data warehouse bin file to this scenario.  It will save the dimbaseline immediately,
        bypassing the save step.  This means that any file of the same type added AFTER this call will overwrite it
        for the scenario.

        :param dbf: DimBinFile to be attached to this scenario
        :type dbf: int or DimBinFiles
        :returns: True if file was added
        :raises: TypeError, ValueError, ObjectDoesNotExist
        """
        if self.dimbaseline is None or not self.dimbaseline.id:
            raise ValueError("Baseline must be saved before appending Data Warehouse Bin Files")

        if isinstance(dbf, DimBinFiles):
            if not dbf.id:
                raise ValueError("DimBinFiles instance must already be saved")
        elif isinstance(dbf, int):
            qs = DimBinFiles.objects.filter(pk=dbf).defer('content')
            if not qs.exists():
                raise ObjectDoesNotExist("No DimBinFile was found with id %s" % dbf)
            dbf = qs[0]
        else:
            raise TypeError("Parameter dbf must be a DimBinFiles instance OR an integer, found type %s" % type(dbf))

        if not self.is_saved:
            self.save()

        # if self.has_required_files and self.is_approved:
        #     self._new_save_baseline_version()
        self._check_files(dbf)
        self.dimbaseline.binfiles.add(dbf)
        self._update()

        return any(map(lambda x: x['id'] == dbf.id, self.files))

    def get_required_files(self):
        """
        This will return the required files list.  Although this list should *NOT* be touched by anybody, it can be
        viewed to allow the user to see what files need to be added for this to be considered complete
        """
        return self.required_filetypes

    def get_files(self):
        """
        This will return a list of file names, descriptions, and types and file ids

        :returns: A list of tuples of the type (id, name, type, description)
        :raises: ObjectDoesNotExist id scenario has not been saved
        """
        if self.dimbaseline is None:
            raise ObjectDoesNotExist("Baseline has not been saved, must be saved before getting file list")

        qs = self.dimbaseline.binfiles.all()
        return [(q.id, q.file_name, q.file_type, q.description) for q in qs]

    def get_file_by_id(self, pk):
        """
        This will get file by file id

        :returns: DimBinFile instance
        :raises: ObjectDoesNotExist if scenario has not been saved
        """
        if self.dimbaseline is None:
            raise ObjectDoesNotExist("Baseline has not been saved, must be saved before getting files")

        qs = self.dimbaseline.dimbinfiles_set.filter(pk=pk)
        if not qs.exists():
            raise ObjectDoesNotExist("No file with id %s is attached to this scenario" % id)
        else:
            return qs[0]

    def get_file_by_type(self, ftype):
        """
        This will get files by type

        If more than one is returned, a queryset will be returned instead of a single DimBinFile instance

        :param ftype: Type of file to get (e.g. config, campaign, input.xml)
        :type ftype: str
        :returns: DimBinFile instance
        :raises: ObjectDoesNotExist if no file can be found with given type or Baseline hasn't been saved
        """
        if self.dimbaseline is None:
            raise ObjectDoesNotExist("Baseline has not been saved, must be saved before getting files")

        qs = self.dimbaseline.binfiles.filter(file_type=ftype)
        if not qs.exists():
            raise ObjectDoesNotExist("No file with type %s is attached to this scenario" % ftype)
        elif len(qs) > 1:
            return qs
        else:
            return qs[0]

    def get_file_by_name(self, name):
        """
        This will get files by name.

        It could return more than one.  If it returns more than one, an error will be raised.

        :return: DimBinFile instance
        :raises: ObjectDoesNotExist if scenario has not been saved, MultipleObjectsReturned
        """
        if self.dimbaseline is None:
            raise ObjectDoesNotExist("Baseline has not been saved, must be saved before getting files")

        qs = self.dimbaseline.dimbinfiles_set.filter(file_name=name)
        if not qs.exists():
            raise ObjectDoesNotExist("No file with name %s is attached to this scenario")
        if len(qs) > 1:
            raise MultipleObjectsReturned("More than one file with name %s was found attached to this scenario")

        return qs[0]

    def get_file(self, name=None, pk=None, ftype=None):
        """
        This method hides the get_file_by_name and get_file_by_id methods into a convenient method where the keyword
        sent in determines the method used.  At least one keyword has to be specified.

        :param name: (Optional) Name of the file to be retrieved
        :type name: str
        :param pk: (Optional) Primary Key (ID) of the file to be retrieved
        :type pk: int
        :param ftype: (Optional) Type of the file to be retrieved
        :type ftype: str
        :returns: DimBinFile instance
        :raises: ValueError if no keyword was specified, ObjectDoesNotExist if no file can be found, or the scenario
                hasn't been saved, MultipleObjectsReturned if the search criteria returned more than one file
        """
        try:
            if not name and not pk and not ftype:
                raise ValueError("Either 'name', 'id', or 'type' must be specified")
            if name is not None:
                return self.get_file_by_name(name)
            if pk is not None:
                return self.get_file_by_id(pk)
            if ftype is not None:
                return self.get_file_by_type(ftype)
        except:
            raise

    def get_missing_files(self):
        """
        This will get the file types that are missing, according to the required file types list.

        *NOTE* This does not take into account files that have not been through the save process yet.

        :returns: List of the file types still needed for completion
        """
        type_list = list()
        for f in self.files:
            if f['id'] is None or f['hash'] is None:
                continue
            else:
                type_list.append(f['type'])

        return filter(lambda x: x not in type_list, self.required_filetypes)

    @staticmethod
    def _locate_file(type, hash, name):
        """
        This will locate a DimBinFile by its name, hash, and type.  If it finds one, it will return it, if it does
        not find one, it will create one.
        """

    def _update(self):
        """
        This will update all of the properties relative to the self.dimbaseline.  This is to be called
        after dimbaseline has been updated to point to another object (newer version).  This will keep the "Baseline"
        object current.  This will also set the file list to those added.
        """
        self.id = self.dimbaseline.id
        self._name = self.dimbaseline.name
        self._description = self.dimbaseline.description
        self._is_completed = self.dimbaseline.is_completed
        self._is_public = self.dimbaseline.is_public
        self._is_approved = self.dimbaseline.is_approved
        self._is_deleted = self.dimbaseline.is_deleted
        self._last_edited = self.dimbaseline.last_modified
        self.model = self.dimbaseline.model
        self.model_version = self.dimbaseline.model_version
        self.location = self.dimbaseline.location
        self.template = self.dimbaseline.template
        self.files = self.dimbaseline.file_list()
        self.user = self.dimbaseline.user
        self.version = self.dimbaseline.last_modified
        return self.has_required_files

    def _check_files(self, bfile):
        """
        Here we check to see if any other files of the same type have been attached to the dimbaseline object.  If
        they have, we unlink them in preparation for the new DimBinFile to be saved.

        :param bfile: DimBinFiles instance which will overwrite any other file with this given type
        :type bfile: DimBinFiles
        """
        if not isinstance(bfile, DimBinFiles) or bfile.id is None:
            raise TypeError("File passed in should be a save DimBinFiles instance")

        existing_files = self.dimbaseline.binfiles.filter(file_type=bfile.file_type).defer('content')

        if existing_files.exists():
            for dbf in existing_files:
                self.dimbaseline.binfiles.remove(dbf)
                if len(dbf.dimbaseline_set.all()) == 0:
                    dbf.delete()

        return

    def _compare_against_db(self):
        """
        This will compare the internal state of the Baseline instance with the saved Dimbaseline object.  If there are
        changes, it will return true, otherwise it will return false.

        Because most changes occur synchronously, like adding files, we only check for the things here that are
        not set synchronously.

        :returns: True if changes have been made when compared to attached DimBaseline instance, false otherwise
        """
        return not (self.dimbaseline.name == self._name and
                    self.dimbaseline.description == self._description and
                    self.dimbaseline.model == self.model and
                    self.dimbaseline.model_version == self.model_version and
                    self.dimbaseline.location == self.location and
                    self.dimbaseline.template == self.template and
                    self.dimbaseline.user == self.user)

    def save(self):
        """
        This will save the Baseline instance to a DimBaseline instance in the data warehouse and link against it.  If
        this has already been saved (or has a DimBaseline instance already attached) this will examine the state of
        the Baseline instance and compare it to the DimBaseline instance attached.  If there are discrepancies, the
        DimBaseline object will be updated.

        If this Baseline instance is complete and approved, it will create a new version of the DimBaseline object,
        make the appropriate changes, and then attach it to this Baseline instance and update all internal attributes.

        Here we also check that the model, user, and location (if specified) are of the appropriate types, raising
        TypeErrors if they are not.

        :raises: TypeError if model, user, or location are not DimModel, DimUser, or DimLocation instances respectively
        """
        if not isinstance(self.model, DimModel) or self.model.id is None:
            raise TypeError("Model attached to this Baseline instance must be a saved DimModel instance")
        if not isinstance(self.user, DimUser) or self.user.id is None:
            raise TypeError("User attached to this Baseline instance must be a saved DimUser instance")
        if self.location is not None and (not isinstance(self.location, DimLocation) or self.location.id is None):
            raise TypeError("Location attached to this Baseline instance must be a saved DimLocation instance")
        if self.template is not None and (not isinstance(self.template, DimTemplate) or self.template.id is None):
            raise TypeError("Template attached to this Baseline instance must be a saved DimTemplate instance")
        if self.is_saved:
            self.dimbaseline.location = self.location
            self.dimbaseline.template = self.template
            self.dimbaseline.name = self.name
            self.dimbaseline.model = self.model
            self.dimbaseline.model_version = self.model_version
            self.dimbaseline.user = self.user
            self.dimbaseline.description = self._description
            self.dimbaseline.last_modified = timezone.now()
            self.dimbaseline.save()
            self._update()
        else:
            new_bl = DimBaseline(
                model=self.model,
                model_version=self.model_version,
                user=self.user,
                location=self.location,
                template=self.template,
                name=self._name,
                description=self._description,
                is_completed=False,
                is_deleted=False,
                is_approved=False
            )
            new_bl.save()
            self.dimbaseline = new_bl
            self._update()
        return self.dimbaseline.id, self.has_required_files
