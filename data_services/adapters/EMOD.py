########################################################################################################################
# VECNet CI - Prototype
# Date: 05/02/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
########################################################################################################################

import urllib2
import zipfile
import cStringIO
import json
# import pdb
from model_adapter import Model_Adapter
from data_services.models import DimRun, DimExecution, DimChannel
from django.db.models import ObjectDoesNotExist
from django.db.models import Q

class EMOD_Adapter(Model_Adapter):
    """
    This is the EMOD data adapter for polling the digital library and datawarehouse

    This is a placeholder class for polling the digital library and eventually the datawarehouse
    on behalf of the expert emod interface.  This will return lists of locations and years
    for "complete" data.  Complete data is defined as having all relevant climatological and
    demographic files.

    It inherits many of its calls from the Model_Adapter class.  This is where model
    specific methods, like add_channels live.
    """
    #: Location of the CSV file containing location and link data
    csv_url = 'http://dl-vecnet.crc.nd.edu/downloads/wh246s17n'
    #: This is the zip file handler
    zip_file = None
    #: Model type id, 1 for EMOD, 2 for OM
    model_id = 1
    #: Xpath for seed.  This will be used when generating the manifest file
    seed_path = 'config.json/parameters/Run_Number'
    #: Input files list
    inputFiles = ['config.json','campaign.json']

    def fetch_executions(self, run_id):
        return [exec_id.id for exec_id in DimRun.objects.get(id=run_id).dimexecution_set.all()]


    def fetch_zip(self,link):
        """
        This is a helper method that fetches the actual zip file from the given link.

        :param link: Link to a URL containing a zip.
        :type link: str or unicode
        :returns: 'File-like' handler for the zip
        :raises: urlib2.urlerror
        """
        # TODO If this isn't depricated have it return an error instead of -1
        try:
            self.zip_file = urllib2.urlopen(link,timeout=30)
        except urllib2.URLError:
            print "There was an error in retrieving the zip file at " + link
            return -1

        return self.zip_file

    def fetch_filenames(self, link):
        """
        This method is used to fill the file names in the config.json.  This fetches the appropriate zip file
        and then opens it, reads the filenames, and then returns a dictionary of names to the caller.

        :param link: String that contains the link from the locations_list
        :type link: str or unicode
        :returns: Dictionary
        """
        zip = self.fetch_zip(link)
        zf = zipfile.ZipFile(cStringIO.StringIO(zip.read()))
        for filename in zf.namelist():
            if "emographics" in filename and '.compiled.json' in filename:
                self.filenames['Demographics_Filename'] = {'filename': filename.split('/')[-1], 'link': ''}
            if "tmean" in filename and '.bin' in filename:
                self.filenames['Air_Temperature_Filename'] = {'filename': filename.split('/')[-1], 'link': ''}
                self.filenames['Land_Temperature_Filename'] = {'filename': filename.split('/')[-1], 'link': ''}
            if "air_temp" in filename and '.bin' in filename:
                self.filenames['Air_Temperature_Filename'] = {'filename': filename.split('/')[-1], 'link': ''}
            if "land_temp" in filename and '.bin' in filename:
                self.filenames['Land_Temperature_Filename'] = {'filename': filename.split('/')[-1], 'link': ''}
            if "rain" in filename and '.bin' in filename:
                self.filenames['Rainfall_Filename'] = {'filename': filename.split('/')[-1], 'link': ''}
            if "umid" in filename and '.bin' in filename:
                self.filenames['Relative_Humidity_Filename'] = {'filename': filename.split('/')[-1], 'link': ''}
        return self.filenames

    def add_channels(self, run_id):
        """ This is the add channels method

         Eventually this method will aid in the adding of channels for a given run.  Currently, this list just holds
         the 'golden' variable list, and add them to a given run.

         :param run_id: ID of the run to add channels to
         :type run_id:
        """
        if not isinstance(run_id, int):
            raise TypeError('Run_id should be an int, recevied %s' % type(run_id))
        if not self.valid_user():
            raise Exception('No valid users detected, only valid users can add channels')
        run = DimRun.objects.filter(id=run_id)
        if not run:
            raise ObjectDoesNotExist('No run with id %s exists' % run_id)

        run = run[0]
        non_malaria_gc_list = []
        golden_channel_list = [
            228466,
            228480,
            228494,
            228508,
            228522,
            228536,
            228550,
            228564,
            228578,
            228592,
            228441,
            228455,
            228443,
            228451,
            228450,
            228452
        ]

        if run.simulation_type == 'MALARIA_SIM':
            channel_list = golden_channel_list
        else:
            channel_list = non_malaria_gc_list

        for chan in channel_list:
            channel = DimChannel.objects.get(pk=chan)
            run.dimchannel_set.add(channel)

        return

    def save_run(self, scenario_id, template_id, start_date, name, description, location_ndx,
                timestep_interval, model_id='', duration=0, end_date='', params=list(),
                note='', run_id=-1, as_object=False):
        """
        This is the overridden save_run method.  The difference is that after save_run is called, add_channels is
        then called on the save run to make sure that the golden channels are included.
        The param state is first deleted, allowing the new param state to be established, but only in the case run_id
        is specified.
        """

        run = super(EMOD_Adapter, self).save_run(scenario_id, template_id, start_date, name, description, location_ndx,
                timestep_interval, model_id=model_id, duration=duration, end_date=end_date,
                note=note, run_id=run_id, as_object=as_object)

        if as_object:
            self.add_channels(run.id)
        else:
            self.add_channels(run)

        return run


