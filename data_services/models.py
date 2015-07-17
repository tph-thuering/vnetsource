########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################
import datetime
import hashlib
import json
import logging
import StringIO
import tempfile
from wsgiref.util import FileWrapper
import zipfile
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils import timezone

from change_doc import JCD, Change
from django.contrib.gis.db import models
from django.db import connections
from django.db.models import Sum, Q
from djorm_pgbytea.fields import ByteaField
from jsonfield import JSONField
from vcimanifest.json_merging.merge_tools import merge_list
from vecnet.simulation import sim_model, sim_status

from . import model_specific
from .sim_file_server.conf import get_active_server
from .utils.jcdfield import JCDField
from lib.django_utils import make_choices_tuple
from dateutil.parser import parse

logger = logging.getLogger('prod_logger')


class DimUser(models.Model):
    def __str__(self):
        return self.username
    username = models.CharField(max_length=30, unique=True)
    first_name = models.CharField(max_length=30, null=True, blank=True)
    last_name = models.CharField(max_length=30, null=True, blank=True)
    organization = models.TextField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(null=True)

    @staticmethod
    def public_usernames():
        return ('Test',)

    @staticmethod
    def is_public_username(username):
        # return true if user's name string is a public DimUser.username
        return username in DimUser.public_usernames()

    class Meta:
        db_table = 'dim_user'


class Folder(models.Model):
    """
    This creates a container for simulations.
    """
    class Meta:
        db_table = 'folder'

    name = models.TextField()
    description = models.TextField(null=True)
    parent = models.ForeignKey('self', db_column='parent_key', null=True, blank=True)
    user = models.ForeignKey(DimUser, db_column='user_key', null=False)
    metadata = JSONField(null=True, blank=True)
    time_created = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    time_deleted = models.DateTimeField(null=True)
    sort_order = models.IntegerField()

    def delete(self):
        # if folder is not empty, do not delete
        if not self.is_empty:
            return 'NotEmpty'
        else:
            self.is_deleted = True
            self.save()
            return True

    @property
    def is_empty(self):
        # check for subfolders
        folder_list = Folder.objects.filter(parent=self.id, is_deleted=False)
        # check for scenarios
        scenario_list = DimBaseline.objects.filter(folder=self.id, is_deleted=False)
        if folder_list.count() == 0 and scenario_list.count() == 0:
            return True
        else:
            return False

    def is_folder(self):
        return True


class DimModel(models.Model):
    id = models.IntegerField(primary_key=True)
    model = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'dim_model'

    def __unicode__(self):
        return '%s (id:%d)' % (self.model, self.id)


class DimLocation(models.Model):
    #id = models.IntegerField(primary_key=True)
    admin007 = models.CharField(max_length=255, null=True, blank=True)
    admin0 = models.CharField(max_length=255, null=True, blank=True)
    admin1 = models.CharField(max_length=255, null=True, blank=True)
    admin2 = models.CharField(max_length=255, null=True, blank=True)
    admin3 = models.CharField(max_length=255, null=True, blank=True)
    # Due to the table partition, the base table which this would point to can't accept foreign keys
    # This means that this table is currently decoupled from the gis tables and checks need to be
    # performed manually (which if you use the django ORM to insert should be fine).
    # TODO: Add database side check constraints and update postgresql procedure vecnet_fill_location_from_point
    geom_key = models.IntegerField()

    def name(self):
        name = ''
        if self.admin0:
            name += self.admin0
        if self.admin1:
            name += ', ' + self.admin1
        if self.admin2 and not self.admin1:
            name += ', ' + self.admin2
        if self.admin2 and self.admin1:
            name += ' ' + self.admin2
        if self.admin3:
            name += ' ' + self.admin3
        return name

    def __str__(self):
        return self.name()

    @staticmethod
    def vecnet_fill_location_from_point(lat, long):
        """ This function replaces stored procedure vecnet_fill_location_from_point. It returns location that contains
        point specified by long and lat.

        :param long: Longitude
        :param lat: Latitude
        :return: DimLocation that contains specified point
        """

        conn = connections['default']
        cursor = conn.cursor()
        cursor.execute("SELECT id, s_name, admin_level FROM gis_base_table WHERE ST_CONTAINS(geom, ST_GeomFromText('point(%s %s)', 4326)) ORDER by admin_level DESC;", [long, lat])
        params = {}
        while True:
            # gis_base_table (supposedly) contains all location in the world. However, they stored by admin level
            # say Kimusu district in Kenya is within Kenya borders (there are problem with borders alignments though)
            # In order to get "fully qualified name" for the location - WHO region name, admin0, admin1 and admin2 names
            # we need to fetch all 4 locations in gis_base_table that contains this point and grab their names
            #
            # Example output from the query
            # SELECT id, s_name, admin_level FROM gis_base_table WHERE ST_CONTAINS(geom, ST_GeomFromText('point(12 12)', 4326)) ORDER by admin_level DESC;
            # "id",  "s_name",   "admin_level"
            # 19119, "Damaturu",   2
            # 758,   "Yobe",       1
            # 264,   "Nigeria",    0
            # 5,     "AFRO",      -1

            gis_location = cursor.fetchone()  # Tuple (id, s_name, admin_level)
            if gis_location is None:
                break
            geom_key = gis_location[0]
            s_name = gis_location[1]
            admin_level = gis_location[2]

            if admin_level == -1:
                params['admin007'] = s_name
            elif admin_level == 0:
                params['admin0'] = s_name
            elif admin_level == 1:
                params['admin1'] = s_name
            elif admin_level == 2:
                params['admin2'] = s_name
                params['geom_key'] = geom_key

        location, created = DimLocation.objects.get_or_create(**params)
        cursor.close()
        return location

    class Meta:
        db_table = 'dim_location'

        # Changing model name in Django admin panel to DimLocation
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "DimLocation"
        verbose_name_plural = "DimLocations"


class DimTemplate(models.Model):
    #id = models.IntegerField(primary_key=True)
    template_name = models.CharField(max_length=100)
    description = models.TextField()
    location_key = models.ForeignKey(DimLocation, db_column='location_key', null=True)
    model_key = models.ForeignKey(DimModel, db_column='model_key', null=False)
    model_version = models.CharField(max_length=32, null=False, blank=False)
    user = models.ForeignKey('DimUser', db_column='user_key')
      # shared_with: List of DimUsers should can see this Template on Create New Simulation page
    shared_with = models.ManyToManyField('DimUser', related_name="templates_shared_with", null=True, blank=True)
    version = models.DateTimeField(auto_now=True)
    climate_url = models.TextField(null=True, blank=False)  # URL for binary data in Digital Library
      # climate_start_date: Start date for weather data in yyyy-mm-dd format.
      # For backward compatibility with fetch_locations() function
    climate_start_date = models.TextField(null=True, blank=False)
      # climate_end_date: End date for weather data in yyyy-mm-dd format.
      # For backward compatibility with fetch_locations() function
    climate_end_date = models.TextField(null=True, blank=False)
      # If DimTemplate is not active, is it not returned bu fetch_template_list() function
    active = models.BooleanField()
      # DimTemplate that is recommended as a replacement for inactive template
    superseded_by = models.IntegerField(blank=True, null=True)

    @property
    def simulation_type(self):
        """
        This is the simulation type stored within the input files for this simulation.  It is
        very similar to the DimRun simulation_type property in that *IT IS READ ONLY*, and that it
        will return the simulation type upon demand.

        This uses a package level dictionary of registered functions.  These function all take a template
        instance and returns a string.
        """
        the_type = self.model_key.model
        if the_type not in model_specific.sim_type.keys():
            raise ValueError("Model type %s does not have a simulation type" % the_type)
        func = model_specific.sim_type[the_type]

        return func(self)

    def __unicode__(self):
        return self.template_name

    def get_file_content(self, file_type):
        """ Return content of file from this template
        """
        the_file = self.dimfiles_set.filter(
            file_type=file_type
        )
        return the_file[0].content

    class Meta:
        db_table = 'dim_template'


class DimBinFiles(models.Model):
    """
    This model will be responsible for storing the files used in simulations.

    All files, both of type binary and ascii, will be stored here as a bytea.  Each file should be stored and
    should have a file_name, file_type, and content, as well as the file_hash.
    """
    file_name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    file_type = models.CharField(max_length=100)
    version = models.DateTimeField(auto_now=True)
    file_hash = models.CharField(max_length=32, null=True)
    is_deleted = models.BooleanField(default=False)
    content = ByteaField(null=True)

    @staticmethod
    def prepare_file(filepath):
        """
        This will open/read/and hash the file given at filepath.

        :param filepath: Fully qualified path to the file to be added
        """
        if not isinstance(filepath, (str, unicode,)):
            raise ValueError("File path must be a path, string, or unicode string representing file location")

        try:
            with open(filepath, 'rb') as f:
                data = f.read()
        except IOError:
            raise IOError("No such file or directory: %s" % filepath)
        except Exception as e:
            raise e

        fhash = hashlib.md5(data).hexdigest()
        content = data

        return fhash, content

    @classmethod
    def get_file_types(cls, **kwargs):
        """
        This will return a list of file types in the data warehouse.

        The kwargs are those that a DimBinFiles filter command can take, and this will limit the types by the criteria
        passed in.

        :param kwargs: Keywords that a DimBinFiles filter command can take
        :type kwargs: kwargs
        :returns: List of types for the above kwargs
        :raises:  Re raises all errors from a filter/distinct command
        """

        types = cls.objects.filter(**kwargs).distinct('file_type').values('file_type')

        return [dbf['file_type'] for dbf in types]

    def __init__(self, *args, **kwargs):
        super(DimBinFiles, self).__init__(*args, **kwargs)
        self.fp = None  # File handler

    def __str__(self):
        return self.file_name

    def open(self, mode="r"):
        """
        Returns: File-like object for reading content of DimBinFile.
                 It is user's responsibility to close it when they are finished.
        """
        # If file handle is already open - close it first
        if self.fp is not None:
            self.close()

        # ByteaField is represented as a python string, so using StringIO to spit out file-like object
        if mode == "r":
            self.fp = StringIO.StringIO(self.content)
        elif mode == "w":
            self.fp = StringIO.StringIO()
        elif mode == "a":
            raise RuntimeError("Append mode is not supported currently")
        else:
            raise RuntimeError("Mode %s is not supported" % mode)

        self.mode = mode
        return self.fp

    def close(self):
        """
        Close file handle created by open function and write data to the database if necessary
        """
        # Using StringIO to write to self.content file. If it was modified, we want to save those changes
        if self.mode == "w":
            self.content = self.fp.getvalue()
            # If file was written by user, we can't calculate the hash
            self.file_hash = None
            self.save()

        # Close file
        if self.fp is not None:
            self.fp.close()

        self.fp = None
        delattr(self, "mode")

    class Meta:
        db_table = 'dim_bin_files'
        unique_together = ("file_name", "file_type", "file_hash")


class SimulationGroup(models.Model):
    """
    Represents a group of simulations submitted for execution at the same time.
    """
    submitted_by = models.ForeignKey(DimUser,
                                     help_text='who submitted the group for execution')
    submitted_when = models.DateTimeField(help_text='when was the group submitted',
                                          null=True, blank=True)  # Assigned by job services

    def __str__(self):
        return "%s" % self.id

    def create_om_zip_file(self, name):
        # s = StringIO.StringIO()

        temp = tempfile.TemporaryFile()
        with zipfile.ZipFile(temp, 'w') as sim_file:
            for sim in Simulation.objects.filter(group=self):
                assert sim.model == sim_model.OPEN_MALARIA

                try:
                    input_file = sim.input_files.get(name="scenario.xml")
                    file_name = input_file.metadata.get("filename", "scenario%s.xml" % input_file.id)
                    sim_file.writestr(file_name, input_file.get_contents())
                except ObjectDoesNotExist:
                    raise RuntimeError("Scenario.xml does not exist in simulation #%s" % sim.id)
                try:
                    output_file = sim.simulationoutputfile_set.get(name="output.txt")
                    sim_file.writestr(file_name.replace(".xml", "_output.txt"), output_file.get_contents())
                except ObjectDoesNotExist:
                    pass
                try:
                    continuous_file = sim.simulationoutputfile_set.get(name="ctsout.txt")
                    sim_file.writestr(file_name.replace(".xml", "_ctsout.txt"), continuous_file.get_contents())
                except ObjectDoesNotExist:
                    pass

        wrapper = FileWrapper(temp)
        temp_len = temp.tell()
        temp.seek(0)

        return wrapper, temp_len


class DimBaseline(models.Model):
    """
    This stores fully qualified baselines.  Each scenario has a user who added it, location, name, description,
    model that it is purposed for, and a version in case of editing.
    """
    name = models.TextField()
    description = models.TextField(null=True)
    location = models.ForeignKey(DimLocation, db_column='location_key', null=True)
    template = models.ForeignKey(DimTemplate, null=True, db_column='template_key', blank=True)
    folder = models.ForeignKey(Folder, null=True, db_column='folder_key', blank=True)
    model = models.ForeignKey(DimModel, db_column='model_key', null=False)
    model_version = models.CharField(max_length=32, null=False, blank=False)
    user = models.ForeignKey(DimUser, db_column='user_key', null=False)
    last_modified = models.DateTimeField(auto_now=True)
    is_completed = models.BooleanField(default=False)
    is_public = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    time_deleted = models.DateTimeField(null=True)
    binfiles = models.ManyToManyField(DimBinFiles)
    metadata = JSONField(null=True, blank=True)
    simulation_group = models.ForeignKey(SimulationGroup, null=True, blank=True)

    def __str__(self):
        return self.name

    def add_all_files(self, files):
        """
        Adds all files in the list to the DimBaseline object.  The objects within files must be saved.  If not,
        an error will result.

        :param files: List of saved DimBinFiles to be added to this scenario
        :type files: list
        :raises: ValueError of file in list is not saved
        """
        for f in files:
            self.binfiles.add(f)
        return

    def copy(self):
        """
        This creates a copy of itself and returns the copy's id
        """
        from copy import deepcopy

        copy = deepcopy(self)
        copy.pk = None
        copy.name = copy.name + ' copy'

        copy.save()
        copy.add_all_files(self.binfiles.all().defer('content'))
        # Don't need to make copies of campaign and config: they be copied upon edit
        #copy.add_all_files(self.binfiles.exclude(Q(file_type='campaign') | Q(file_type='config')).defer('content'))

        return copy.id

    def remove_all_files(self):
        """
        This removes all attached binfiles
        """
        qs = self.binfiles.all()
        for f in qs:
            self.binfiles.remove(f)
        return

    def file_list(self):
        """
        This returns a list of dictionaries containing pertinent information about each file attached to this scenario
        """
        qs = self.binfiles.all().defer('content')

        retlist = [
            {
                'id': f.id,
                'name': f.file_name,
                'type': f.file_type,
                'hash': f.file_hash,
                'description': f.description
            }
            for f in qs
        ]
        return retlist

    class Meta:
        db_table = 'dim_baseline'
        unique_together = ("name", "model", "template", "user", "last_modified")
        # Changing model name in Django admin panel to DimBaseline
        # http://stackoverflow.com/questions/8368937/change-model-class-name-in-django-admin-interface
        # https://docs.djangoproject.com/en/1.5//ref/models/options/#verbose-name
        verbose_name = "DimBaseline"
        verbose_name_plural = "DimBaselines"


class DimRun(models.Model):
    model_version = models.CharField(max_length=32, null=False, blank=False)
                                       #related_name='dim_run_start_date_key')
    start_date_key = models.DateTimeField(null=True, blank=True)
                                     #related_name='dim_run_end_date_key')
    end_date_key = models.DateTimeField(null=True, blank=True)
    location_key = models.ForeignKey(DimLocation, null=True, db_column='location_key', blank=True)
    template_key = models.ForeignKey('DimTemplate', null=True, db_column='template_key', blank=True)
    # DimBaseline will replace DimTemplate eventually
    baseline_key = models.ForeignKey('DimBaseline', null=True, db_column='baseline_key', blank=True)
    models_key = models.ForeignKey(DimModel, null=True, db_column='model_key', blank=True)
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    timestep_interval_days = models.IntegerField()
    # base_changes = DictionaryField()
    status = models.CharField(max_length=100)
    time_launched = models.DateTimeField(null=True)
    time_created = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    time_deleted = models.DateTimeField(null=True, blank=True)
    jcd = JCDField(null=True, blank=True)
    metadata = JSONField(null=True, blank=True)
    # objects = HStoreManager()
    csv_output = models.ForeignKey('SimulationInputFile', null=True, blank=True)

    def numjobs(self, reps_per_exec=1):
        #TODO update documentation to include non-manifest, or remove non-manifest (whichever happens first)
        """
        This returns the total number of replications being sent to the cluster for calculation

        This will use the jcd expand method to calculate the number of executions.  The number of
        replications, therefore, is the number of executions multiplied by the number of replications
        per execution.

        We also check to make sure the JCD has been set for this run.  The run does not need to be saved
        necessarily, but a valid JCD has to be set for the run.  If it is not, an exception will be raised
        explaining such.

        :param reps_per_exec: Optional argument that is the number of replications per execution, defaults to 1
        :type reps_per_exec: int
        :returns: Integer representing total number of jobs being sent to the cluster for calculation
        """
        if self.jcd is None:
            # old-style (non-manifest) numjobs
            raise NotImplemented("hstore-based runs are depricated")

        (rl_jcd, num_executions, jcd_list) = self.jcd.expand()

        return num_executions * reps_per_exec

    def expand_executions(self, reps_per_exec, rl_jcd_only=False):
        """
        This will expand the executions for this run.  It will do so by looping over the entire jcd.expand
        result and then create a run level jcd, and a list of executions.  This will then need
        to be iterated over if it is to be used with a manifest file.

        *NOTE* This is *NO LONGER* a generator method, this now takes the reps_per_exec and then spits out a tuple
        where the first value is the run level jcd and the second is a list of executions.

        Until JCD is fully supported, this will check to make sure that the JCD is not null.

        Since an expansion of the run cannot happen, but a launching of the run can happen after execution, we
        need a way to get at the run level jcd.  As such, we add a flag to this method that will allow for only
        the run level jcd to be generated and returned.

        :param reps_per_exec: Replications per execution desired
        :type reps_per_exec: int
        :param rl_jcd_only: Flag indicating the the run level JCD needs to be returned
        :type rl_jcd_only: bool
        :returns: Tuple of (run_level_jcd, [executions])
        :raises: ValueError
        """
        # TODO:  Add tests for rl_jcd_only
        if not self.jcd:
            raise ValueError("JCD is not set for this run")

        jcd = self.jcd

        (rl_jcd, num_executions, jcd_list) = jcd.expand()

        if rl_jcd_only:
            return rl_jcd, []

        if len(self.dimexecution_set.all()) > 0:
            raise ValueError("Run %s has already been expanded" % self.id)

        execution_list = list()
        if num_executions == 1:
            new_execution = DimExecution(
                run_key=self,
                name=self.name,
                replications=reps_per_exec,
                jcd=JCD()
            )
            new_execution.save()
            return rl_jcd, [new_execution]
        else:
            for doc in jcd_list:
                new_execution = DimExecution(
                    run_key=self,
                    name=self.name_from_sweeps(doc.change_list),
                    replications=reps_per_exec,
                    jcd=doc
                )
                new_execution.save()
                execution_list.append(new_execution)
            return rl_jcd, execution_list

    @classmethod
    def name_from_sweeps(cls, iterations):
        """
        This will generate a name for an execution given a single realization of the facorial expansion

        :param iterations: Realization of the factorial expansion
        :type iterations: list
        :returns: Name as a string
        """
        name_list = list()
        for value in iterations:
            if isinstance(value, dict):
                for key, entry in value.iteritems():
                    k = key.split('/')[-1]
                    name_list.append("%s is %s" % (k, entry))

        return ' and '.join(name_list)

    @property
    def simulation_type(self):
        """
        This property allows introspection of the Template files  for this run to determine its
        simulation type.  This will use a package level dictionary to determine which function
        to call.

        As the package level dictionary is updated (and specific functions are registered there), they
        will become available here.  The API is as follows:  The method should take a DimRun instance
        and return a string (or unicode) representing the vector type.

        *NOTE* This attribute is read only and will raise an AttributeError if you try to set it.
        """
        template = self.template_key
        the_type = self.models_key.model
        if the_type not in model_specific.sim_type.keys():
            raise ValueError("Model type %s does not have a simulation type method" % the_type)
        func = model_specific.sim_type[the_type]
        return func(template)

    def get_tuple(self):
        """
        This is the get_tuples method.

        The Open Malaria team requested that it be possible to get a list of tuples regarding database information
        stored for a run.  This used to be in the run_status method in the adapter and has since been moved to here.

        :returns: List of tuples containing exec_id and the number of replications
        """
        tuple_list = list()
        executions = self.dimexecution_set.all().order_by('id')
        for execs in executions:
            counter = execs.dimreplication_set.all().count()
            tuple_list.append((execs.id, counter))
        return tuple_list

    def set_status(self):
        """
        This is the set status method.

        This will query the database, and determine the number of completed and failed replications.

        :returns: A tuple of number of replications, number completed successfully, number failed
        """
        launched = DimExecution.objects.filter(
            run_key=self
        ).count()

        if launched == 0:
            if self.status is not None:
                self.status = None
                self.save()
            return None

        total_replications = DimExecution.objects.filter(run_key_id=self).aggregate(Sum('replications'))['replications__sum']
        #total_replications = DimReplication.objects.filter(execution_key__run_key=self).count()
        completed_replications = DimReplication.objects.filter(
            status=0,
            execution_key__run_key=self
        ).count()

        errored_replications = DimReplication.objects.filter(
            status=-1,
            execution_key__run_key=self
        ).count()

        self.status = "%s/%s/%s" % (completed_replications, total_replications, errored_replications)

        self.save()

        return completed_replications, total_replications, errored_replications

    def get_status(self):
        """
        This gets the status of the run as a triple (num_reps, num_completed, and num_failed).

        If the status field is not null, then it is assumed that the status is a string stored in:
        num_reps/num_completed/num_failed format.

        It will attempt to parse as such.  If it fails to parse as such, the "get_status" method will be called and
        the results of that will be placed into the status field.
        """
        if self.status is not None:
            try:
                tup = self.status.split('/')
                num_total = int(tup[0])
                num_complete = int(tup[1])
                num_failed = int(tup[2])
                return num_total, num_complete, num_failed
            except ValueError:
                # This corrects any errors currently stored
                return self.set_status()
            except IndexError:
                # This corrects if a 'x/x' is saved in place
                return self.set_status()
        else:
            return self.set_status()

    @property
    def storage_method(self):
        """
        We currently have an obligation to support both change storage methods (hstore and JCD) until the JCD has been
        universally adopted and implmented.  To help with this, the run object itself will carry the logic to determine
        the backend storage medium for changes.

        Since all executions of a particular run will have something in JCD or hstore fields, we examine just the first
        execution.  If leans one way or the other, the run leans that way.

        We use the logic table below:
            |   hstore      |   JCD     |   result                      |
            -------------------------------------------------------------
            |  not blank    |   blank   |   hstore                      |
            |   blank       | not blank |   JCD                         |
            |   blank       |   blank   |   Doesn't matter (JCD)        |
            |  not blank    | not blank |   JCD (JCD takes precedence)  |
        """
        # execution = self.dimexecution_set.all()[0]
        if self.jcd is None:
            return 'hstore'
        else:
            return 'jcd'

    def set_input_files(self, files, sweeps=None):
        """ Set input files for this run using JCD
        Note that due to JCD limitations each input file should be valid JSON document represented as a string

        :param files: Dictionary of input files. Key is filename, and value is content of the file
        :type  files: dict
        :param sweeps: Dictionary of sweeps. Key is an xpath, and value is sweep definition
                       (| separated or in 1:3:1 format)
        :type sweeps: dict

        :raises: **ValueError** - if incorrect sweep definition is provided
        """

        # Clear hstore information in HSTORE (if any)
        # Needed for backward compatibility with hstore-based runs
        # param_objs = DiParamState.mobjects.filter(run_key=self.pk)
        # for param in param_objs:
        #     # https://docs.djangoproject.com/en/1.5/ref/models/instances/#deleting-objects
        #     # Issues an SQL DELETE for the object. This only deletes the object in the database; the Python instance
        #     # will still exist and will still have data in its fields.
        #     param.delete()

        # Build JCD from the list of input files.
        ch_list = []
        for filename, content in files.iteritems():
            # Use node replacement and update content of specified input file in this run's JCD.
            node = Change.node(filename,  # Name of the node.
                               [{filename: json.loads(content)}],  # List of dictionaries containing changes.
                               mode="-"  # mode: replace (aka "Truncate" in JCD terminology)
                                         # There are two other modes: "+" and "~", but we don't use then here
                               )
            ch_list.append(node)

        if sweeps is not None:
            # Add sweeps to JCD
            for xpath, value in sweeps.iteritems():
                key = xpath.split('/')[-1]
                if ':' in value or '|' in value:
                    if ':' in value:
                    # ("start", "stop", "step", "xpath")
                        try:
                            kwargs = {"xpath": xpath,
                                      "start": value.split(":")[0],
                                      "stop": value.split(":")[1],
                                      "step": value.split(":")[2]}
                        except IndexError:
                            raise ValueError("Incorrect sweep value %s for xpath %s", (value, xpath))
                        ch_list.append(Change.sweep(name=key, **kwargs))
                    else:
                        kwargs = {"xpath": xpath + key,
                                  "l_vals": value.split("|")}
                        ch_list.append(Change.sweep(name=key, **kwargs))
                else:
                    raise ValueError("Incorrect sweep value %s for xpath %s", (value, xpath))
        jcd = JCD.from_changes(ch_list)

        # Apply JCD to the run and save it to the database
        self.jcd = jcd
        self.save()

    def get_input_files(self):
        """ Returns input files for EMOD DimRun. Doesn't work with OpenMalaria DimRuns yet.
        Works with both JCD and hstore-based runs.
        For runs with sweeps returns "basic" input files, before sweeps are applied
        """
        template_input_files = dict()
        if self.jcd is not None:
            # JCD-based run
            # Use merge_list to produce input files

            rlcl = self.jcd.jcdict
            dim_template_files = self.template_key.dimfiles_set.all()
            for dimfile in dim_template_files:
                template_input_files[dimfile.file_type] = json.loads(dimfile.content)
            # Judging by split_executions function, merge_list works with sweeps properly (i.e. ignores them)
            input_files = merge_list(template_input_files, rlcl)
            # merge_list returns EMOD input files as python dictionaries, so converting them to string
            for input_file in input_files:
                input_files[input_file] = json.dumps(input_files[input_file])
            return input_files
        else:
            # Non JCD run.
            # Use old good inputFile.createChanges()
            raise RuntimeError("Support for hstore-based runs has been depricated")
            # execution_id = self.dimexecution_set.all()[0].pk
            # input_files = data_services.lib.inputFile.createChanges(execution_id)
            # # createChanges function (apparently) returns EMOD input files as python dictionaries.
            # # converting them to strings
            # for key, value in input_files.iteritems():
            #     input_files[key] = json.dumps(value)
            # return input_files

    def has_sweeps(self):
        if self.jcd is None:
            raise ValueError("has_sweeps is not supported on non-JCD runs")

        for change in self.jcd.change_list:
            if change.type == "sweep":
                return True
        return False

    def get_sweeps(self):
        if self.jcd is None:
            raise ValueError("get_sweeps is not supported on non-JCD runs")

        if self.has_sweeps() is False:
            return None

        jcd = self.jcd
        sweeps = list()
        for change in jcd.change_list:
            # JCD is a list of Change object that will be applied by expand_sweep function later
            # Change can be either atomic change or a sweep
            # (node replacement is not supported in this version)

            if change.type == "sweep":
                # Sweep is defined as a JSON dictionary, for example
                #	"Demographic_Coverage": {
                #       "Changes": [{
                #	        "campaign.json/Events/0/Event_Coordinator_Config/Demographic_Coverage": "0.3:0.8:0.1"
                #       }]
                #   },
                #
                #  "Acquisition_Blocking_Immunity_Decay_Rate":
                #     {"Changes": [{"config.json/parameters/Acquisition_Blocking_Immunity_Decay_Rate": "5|10"}]},
                #
                # We extract xpath and sweep definition from this dictionary using code snippet below
                sweep_path = change.jcd_objects[0].jcdict["Changes"][0].keys()[0]
                sweep_values = change.jcd_objects[0].jcdict["Changes"][0][sweep_path]
                sweeps.append({sweep_path: sweep_values})

        return sweeps

    class Meta:
        db_table = 'dim_run'

    def __str__(self):
        return "%s: %s" % (self.id, self.name)


class DimExecution(models.Model):
    # id = models.IntegerField(primary_key=True)
    run_key = models.ForeignKey('DimRun', null=True, db_column='run_key', blank=True)
    name = models.CharField(max_length=255, blank=True)
    #xpath_changes = DictionaryField()
    replications = models.IntegerField(null=True, blank=True, default=0)
    jcd = JCDField(null=True)
    #objects = HStoreManager()

    def expand_replications(self, reps_per_exec):
        """
        This will create replications for this particular execution.  The reps_per_exec
        will determine how many replications to be created.  A list of the replications
        are returned to the caller.  This is not a generator as there is no means to
        currently control this process.  However, that can change in the future.

        :param reps_per_exec: Number of replications per DimExecution
        :returns: List of replications
        """
        series_id = 0
        rep_list = list()
        for rep in range(0, reps_per_exec):
            replication = DimReplication(
                seed_used=0,
                series_id=series_id,
                execution_key=self
            )
            replication.save()
            series_id += 1
            rep_list.append(replication)

        return rep_list

    class Meta:
        
        db_table = 'dim_execution'


class DimReplication(models.Model):
    # id = models.IntegerField(primary_key=True)
    time_started = models.DateTimeField(null=True, blank=True)
    time_completed = models.DateTimeField(null=True, blank=True)
    seed_used = models.IntegerField()
    series_id = models.IntegerField()
    execution_key = models.ForeignKey(DimExecution, db_column='execution_key')
    status = models.IntegerField(null=True)
    status_text = models.TextField(null=True)

    class Meta:
        db_table = 'dim_replication'


class DimChannel(models.Model):
    # id = models.IntegerField(primary_key=True)
    # replication_key = models.ForeignKey('DimReplication', null=True, db_column='replication_key', blank=True)
    title = models.CharField(max_length=100, blank=True)
    type = models.CharField(max_length=100, blank=True, null=True)
    units = models.CharField(max_length=100, blank=True, null=True)
    file_name = models.CharField(max_length=100, blank=True)
    runs = models.ManyToManyField(DimRun)

    class Meta:
        
        db_table = 'dim_channel'


class DimNotes(models.Model):
    # id = models.IntegerField(primary_key=True)
    run_key = models.ForeignKey(DimRun, db_column='run_key')
    notes = models.TextField()

    class Meta:
        
        db_table = 'dim_notes'


class DimFiles(models.Model):
    file_name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    file_type = models.CharField(max_length=100)
    content = models.TextField()
    templates = models.ManyToManyField(DimTemplate)
    version = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dim_files'

    def __str__(self):
        return "%s : %s" % (self.pk, self.file_name)


class BaseFactData(models.Model):
    timestep = models.IntegerField()
    value = models.FloatField()
    channel_key = models.ForeignKey(DimChannel, db_column='channel_key')
    run_key = models.ForeignKey(DimRun, db_column='run_key')
    replication_key = models.ForeignKey(DimReplication, db_column='replication_key')

    class Meta:
        db_table = 'base_fact_data'
        
        # Not allowing django to manage this as it is a base table for all other data tables
        #managed = False


class FactData(models.Model):
    channel_key = models.ForeignKey(DimChannel, db_column='channel_key')
    timestep = models.IntegerField()
    time_created = models.DateTimeField(auto_now=True)
    value = models.FloatField()
    channel_key = models.IntegerField()
    run_key = models.IntegerField()
    replication_key = models.IntegerField()

    class Meta:
        db_table = 'fact_data'


class GisBaseTable(models.Model):

    class Meta:
        db_table = 'gis_base_table'
        
    geom = models.MultiPolygonField()
    s_name = models.CharField(max_length=100)
    s_desc = models.TextField(null=True, blank=True)
    admin_level = models.IntegerField()
    objects = models.GeoManager()

    def __str__(self):
        return "%s (%s)" % (self.s_name, self.admin_level)


class Simulation(models.Model):
    """
    Represents a single execution of a simulation model.  Contains sufficient information about the particular
    simulation model that was run and the input data so that the output data can be reproduced.
    """
    group = models.ForeignKey(SimulationGroup, related_name='simulations')
    model = models.CharField(help_text='simulation model ID',
                             choices=make_choices_tuple(sim_model.ALL, sim_model.get_name),
                             max_length=sim_model.MAX_LENGTH)
    version = models.CharField(help_text='version of simulation model',
                               max_length=20)
                               #  Format varies from model to model; i.e., it's model specific
    cmd_line_args = models.CharField(help_text='additional command line arguments passed to the model',
                                     max_length=100,
                                     blank=True)
    status = models.CharField(help_text='status of the simulation',
                              choices=make_choices_tuple(sim_status.ALL, sim_status.get_description),
                              max_length=sim_status.MAX_LENGTH)
    started_when = models.DateTimeField(help_text='when was the simulation started',
                                        null=True, blank=True)  # Collected on the cluster
    duration = models.BigIntegerField(help_text='how long the simulation ran (in seconds)',
                                      null=True, blank=True)  # Collected on the cluster

    @property
    def duration_as_timedelta(self):
        """
        Get the simulation's duration as a Python timedelta object.
        """
        if self.duration is None:
            return None
        return datetime.timedelta(seconds=self.duration)

    @property
    def ended_when(self):
        """
        When did the simulation end (either successfully or due to error).

        :return datetime: Date and time when the simulation stopped, or None if it has not yet started or is still
                          running.
        """
        if self.started_when is None or self.duration is None:
            return None
        return self.started_when + self.duration_as_timedelta

    def copy(self, include_output=False, should_link_files=False):
        simulation_group = SimulationGroup(submitted_by=self.group.submitted_by)
        simulation_group.save()

        new_simulation = Simulation.objects.create(
            group=simulation_group,
            model=self.model,
            version=self.version,
            status=sim_status.READY_TO_RUN
        )

        # Add simulation input files to the new simulation
        for input_file in self.input_files.all():
            if should_link_files:
                new_simulation.input_files.add(input_file)
            else:
                new_simulation.input_files.add(input_file.copy())

        if include_output:
            # Add simulation output files to the new simulation
            for output_file in self.output_files.all():
                new_simulation.output_files.add(output_file.copy())

        return new_simulation

    def __str__(self):
        return "%s (%s v%s) - %s" % (self.id, self.model, self.version, self.status)


class SimulationFile(models.Model):
    """
    Base class for a simulation's data file (input files and output files).
    """
    class Meta:
        abstract = True

    class MetadataKeys:
        CHECKSUM = 'checksum'  # For verifying downloads of the file and accidental corruption on file server
        CHECKSUM_ALGORITHM = 'checksum_alg'

    class ChecksumAlgorithms:
        MD5 = 'MD5'

    name = models.TextField(help_text="file's name (e.g., 'ctsout.txt', 'config.json')")
                            # Within a single simulation, a data file's name is unique.  No two input files share the
                            # the same name, nor do any two output files.
    uri = models.TextField(help_text="where the file's contents are stored")
                          # In the long term, this points to a file storage service/server (e.g., WebDAV, MongoDB, ...)
                          # As short-term approach, the contents can be stored in this field using the "data:" scheme
                          #    http://en.wikipedia.org/wiki/Data_URI_scheme
    metadata = JSONField(help_text="additional info about the file, e.g., its data format")
                         # If we discover that a particular metadata field is queried a lot, we can optimize the queries
                         # in several ways (explicit indexes in another table; moved the field into its own model field,
                         # etc).

    def get_contents(self):
        """
        Read all the bytes in the file.

        :returns str: The file's contents
        """
        with self.open_for_reading() as f:
            contents = f.read()
        return contents

    def open_for_reading(self):
        """
        Opens the file so its contents can be read in binary mode.

        :returns: A file-like object with at least a read() method.  It's also a context manager so it can be used in a
                  "with" statement.
        """
        file_server = get_active_server()
        file_like_obj = file_server.open_for_reading(self.uri)
        return file_like_obj

    def _set_contents(self, contents, is_binary=True):
        file_server = get_active_server()
        (self.uri, md5_hash) = file_server.store_file(contents)
        self.metadata = {
            self.MetadataKeys.CHECKSUM: md5_hash,
            self.MetadataKeys.CHECKSUM_ALGORITHM: 'MD5',
        }
        self.save()

    def copy(self):
        if isinstance(self, SimulationInputFile):
            new_simulation_file = SimulationInputFile.objects.create_file(
                contents=self.get_contents(),
                name=self.name,
                metadata=self.metadata,
                created_by=self.created_by
            )
        elif isinstance(self, SimulationOutputFile):
            new_simulation_file = SimulationOutputFile.objects.create_file(
                contents=self.get_contents(),
                name=self.name,
                metadata=self.metadata,
            )
        else:
            raise Exception("SimulationFile is not of type SimulationInputFile nor SimulationOutputFile")

        return new_simulation_file

    def __str__(self):
        return "%s - %s" % (self.id, self.name)


class SimulationFileModelManager(models.Manager):
    """
    Custom model manager for the data models representing simulation files.
    """

    def create_file(self, contents, **kwargs):
        sim_file = self.create(**kwargs)
        sim_file._set_contents(contents)
        return sim_file


class SimulationInputFile(SimulationFile):
    """
    An input file for a simulation.  An input file can be shared among multiple simulations.  An input file is
    immutable since it represents all or some of the data fed into a particular execution of the simulation model.  If
    it is altered, then it's no longer possible to reproduce the output from the simulation.

    An input file at this conceptual level is different than the concept at the user's perspective.  From her viewpoint,
    an input file is mutable.  For example, an OpenMalaria user can create a scenario file and then run a simulation
    with it.  After examining the simulation's output, she makes some changes in the scenario and re-runs it.  From her
    perspective, the two simulations were run with different versions of a single scenario file.  Those two versions
    of that scenario file would be represented by two instances of this class.  Their relationship as snapshots of the
    same scenario file would be stored in another data model.
    """
    simulations = models.ManyToManyField(Simulation,
                                         help_text='the simulations that used this file as input',
                                         related_name='input_files')
    created_by = models.ForeignKey(DimUser,
                                   help_text='who created the file')
    created_when = models.DateTimeField(help_text='when was the file created',
                                        auto_now_add=True)

    objects = SimulationFileModelManager()

    def set_contents(self, contents):
        simulations = self.simulations.all()

        if len(simulations) > 1:
            raise RuntimeError("File is shared by multiple simulations.")

        if len(simulations) == 0 or simulations[0].status == sim_status.READY_TO_RUN:
            self._set_contents(contents)
        else:
            raise RuntimeError("Simulation is not ready to run.")


class SimulationOutputFile(SimulationFile):
    """
    An output file produced by a simulation.
    """
    simulation = models.ForeignKey(Simulation,
                                   null=True,
                                   blank=True,
                                   help_text='the simulation that produced this file')

    objects = SimulationFileModelManager()


class RunMetaData():
    class Intervention:
        data_dict = {
            "IRSHousingModification": "Indoor Residual Spraying (IRS)",
            "SimpleBednet": "Long Lasting Insecticidal Nets (LLIN)",
            "InsectKillingFence": "Insect Killing Fence",
        }

        def __init__(self, intervention):
            self.intervention = intervention
            # some interventions do not have a class field, fix it, it it's "Simple Bednets (predefined)"
            try:
                self.type = intervention['Event_Coordinator_Config']['Intervention_Config']['class']
                if self.type == "AntimalarialDrug":
                    self.name = intervention['Event_Coordinator_Config']['Intervention_Config']["Drug_Type"] + " Drug"
                else:
                    self.name = self.data_dict.get(self.type, self.type)
            except KeyError:
                if "Simple_Bednets_(predefined)" == intervention['Event_Coordinator_Config']['Intervention_Config']['my_name']:
                    self.type = "SimpleBednet"
                    self.name = self.data_dict.get(self.type, self.type)

        def __str__(self):
            return self.name

    results_base_url = 'https://ci.vecnet.org/ts_emod/output/results_viewer/'

    def __init__(self, dimRun):
        self.dimRun = dimRun
        self.getMetaData()

    def getMetaData(self):
        # Stuff retrieved from derived
        dimRun = self.dimRun
        scenario = dimRun.baseline_key
        if not scenario:
            raise RuntimeError("Run is not associated with a baseline.")
        location = dimRun.location_key
        user = scenario.user  # use created_by_key instead
        inputFiles = dimRun.get_input_files()
        configFile = inputFiles['config.json']
        configJson = json.loads(configFile)
        campaignFile = inputFiles['campaign.json']
        campaignJson = json.loads(campaignFile)
        metaData = dimRun.metadata

        self.coordinates = []
        self.species = []

        self.username = user.username

        if user.first_name and user.last_name:
            self.creator = user.first_name + " " + user.last_name
        else:
            self.creator = self.username

        if user.organization:
            self.creator += ", " + user.organization

        self.results_url = settings.SITE_ROOT_URL.strip("/") + reverse("ts_emod_run_details", args=[dimRun.id,])
        self.location = location.name()
        self.coordinates = self.getCoordinates()
        self.time_period = [dimRun.start_date_key, dimRun.end_date_key]
        for specie in configJson['parameters']['Vector_Species_Params']:
            self.species.append("An. " + specie)

        interventions = list()
        for intervention in campaignJson['Events']:
            interventions.append(self.Intervention(intervention))
        self.interventions = [intervention.name for intervention in interventions]
        self.interventions_set = list(set(self.interventions))
        self.model_version = dimRun.model_version
        self.simulation_type = configJson['parameters']['Simulation_Type']
        self.run_date = dimRun.time_launched

        # Stuff retrieved from database
        if metaData is None:
            metaData = {}

        self.is_public = metaData.get('isPublic', 'True')
        self.title = self.dimRun.name  # metaData.get('title', '')
        self.citation = metaData.get('citation', '')
        self.tags = metaData.get('tags', '')
        self.description = metaData.get('description', '')
        self.parameters_of_interest = metaData.get('parametersOfInterest', '')
        try:
            # dateutil.parser.parse
            self.metadata_last_update_date = parse(metaData['metaDataLastUpdateDate'])
        except (KeyError, TypeError):
            # KeyError if metaDataLastUpdateDate is not defined
            # TypeError if timestamp parsing fails
            self.metadata_last_update_date = self.run_date
        if self.metadata_last_update_date is None:
            # Run hasn't been launched yet
            self.metadata_last_update_date = timezone.now()

        # Generate autoname/autoid
        interventions_label = ""
        unique_labels = set()
        for intervention in interventions:
            unique_labels.add(intervention.type)
        for label in unique_labels:
            interventions_label += label + "_"
        interventions_label = interventions_label[0:-1]

        days = (dimRun.end_date_key - dimRun.start_date_key).days
        if days < 365:
            duration = "%sm" % (days / 30)
        else:
            duration = "%sy" % (days / 365)
        self.autoname = "run_" + \
                        str(self.dimRun.id) + "_" +\
                        str(self.username) + "_" + \
                        str(interventions_label) + "_" + \
                        str(self.location.replace(" ", "").replace(",", "")) + "_" + \
                        str(duration)


    def getMetaData_as_JSON(self):
        self.getMetaData()
        self.as_json = {}
        self.as_json.update({'ID': self.dimRun.id})
        self.as_json.update({'Name': self.autoname})
        self.as_json.update({'Title': self.title})
        self.as_json.update({'Creator': self.creator})
        self.as_json.update({'Cite as': self.citation})
        self.as_json.update({'URL': self.results_url})
        self.as_json.update({'Location': self.location})
        self.as_json.update({'Latitude': self.coordinates['latitude']})
        self.as_json.update({'Longitude': self.coordinates['longitude']})
        self.as_json.update({'Time Period of Simulation': datetime.datetime.strftime(self.time_period[0], '%b. %d, %Y')
                                                       + ', midnight - ' +
                                                         datetime.datetime.strftime(self.time_period[1], '%b. %d, %Y')
                                                       + ', midnight'})
        self.as_json.update({'Description': self.description})
        self.as_json.update({'Species': self.species})
        self.as_json.update({'Interventions': self.interventions_set})
        self.as_json.update({'Parameters of Interest': self.parameters_of_interest})
        self.as_json.update({'Tags': self.tags})
        self.as_json.update({'Model': self.model_version})
        if self.run_date is not None:
            self.as_json.update({'RunDate': datetime.datetime.strftime(self.run_date, '%b. %d, %Y, %X')})
        self.as_json.update({'MetaData Last Updated':
                            datetime.datetime.strftime(self.metadata_last_update_date, "%Y-%m-%dT%XZ%z")})
        # if type(self.metadata_last_update_date) in (str, unicode):
        #     self.as_json.update({'MetaData Last Updated': self.metadata_last_update_date})
        # elif self.metadata_last_update_date is not None:
        #     self.as_json.update({'MetaData Last Updated': datetime.datetime.strftime(self.metadata_last_update_date, '%b. %d, %Y, %X')})
        # metadata_last_update_date in ISO-8601 format
        # datetime.strftime(self.metadata_last_update_date, "%Y-%m-%dT%XZ%z")

    def getCoordinates(self):
        location = GisBaseTable.objects.all().filter(id=self.dimRun.location_key.geom_key)
        # Ignore PyCharm warning below
        # GisBaseTable.objects is models.GeoManager() and it does produce GeoQuerySet which has centroid function
        # Somehow PyCharm thinks it is normal QuerySet
        # Please refer to https://docs.djangoproject.com/en/dev/ref/contrib/gis/geoquerysets/#centroid for more details
        try:
            centroid = location.centroid(model_att='centroid')[0].centroid
            latitude = centroid.y
            longitude = centroid.x
        except:
            latitude = 'NA'
            longitude = 'NA'

        return {'latitude': latitude, 'longitude': longitude}

    def saveMetaData(self):
        if self.dimRun.metadata is None:
            self.dimRun.metadata = {}

        self.dimRun.metadata['isPublic'] = self.is_public
        #self.dimRun.metadata['title'] = self.title
        self.dimRun.name = self.title
        self.dimRun.metadata['citation'] = self.citation
        self.dimRun.metadata['tags'] = self.tags
        self.dimRun.metadata['description'] = self.description
        self.dimRun.metadata['parametersOfInterest'] = self.parameters_of_interest
        self.dimRun.metadata['metaDataLastUpdateDate'] = timezone.now()
        self.dimRun.save()
