########################################################################################################################
# VECNet CI - Prototype
# Date: 05/02/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
########################################################################################################################


import shutil
import uuid
import json
import os
import psycopg2
import datetime
from io import BytesIO
from struct import pack
from django.db import connections, transaction
from django.core.exceptions import ObjectDoesNotExist
from data_services.ingesters.base_ingester import Base_ingester
from data_services.models import DimReplication, DimChannel, BaseFactData, DimExecution, SimulationInputFile
from data_services.utils import encode_binary, commit_to_warehouse
import pdb
import os
from vecnet.emod.output import convert_to_csv


class EMOD_ingester(Base_ingester):
    """This is the ingestion script for the EMOD malaria model.  This will take values
    from output files that EMOD creates and fill tables within the VECNet CI
    datawarehouse
    """

    FileList = dict()   #:
    DataList = list()   #:

    def __init__(self, zip_file=None, execid=None, seriesid=None, chan_list=None, msg=None):
        """
        This init method will take several arguments and use those to ingest data into the vecnet-CI datawarehouse

        This takes a zip file (the path to the zip file), execid, seriesid, and chan_list.  Given this information,
        this ingester will create a replication, and then fill that replication with the data in the zip file.  If
        execid and/or seriesid are not specified, the filename is assumed to be of the type "REPID-XXXX.zip" where
        the replication id will be parsed from the file name.

        :param str zip_file: A path to a zip file on the file system.
        :raises TypeError: When any file address is not of type str
        :raises ObjectDoesNotExist: When the replication_id given does not exist in the data warehouse
        """
        self.FileList = dict()
        self.DataList = dict()
        self.alreadyIngested = None
        # the files needed by EMOD
        self.FILES_OF_INTEREST = ('DemographicsSummary', 'VectorSpeciesReport', 'InsetChart', 'BinnedReport')
        # create a unique temporary directory for the needed files
        self.BASE_PATH = os.path.sep + 'tmp'
        self.temporary_path = self.BASE_PATH + os.path.sep + str(uuid.uuid4())
        # get the replication ID from the filename. filename is expected to be of the following format
        #   path/to/file/file_name-replication_number.zip

        if not execid and not seriesid:
            replication_id = int(os.path.basename(zip_file).strip(".zip").split("-")[1])
            try:
                self.replication = DimReplication.objects.get(pk=replication_id)
            except:
                raise ObjectDoesNotExist('No replication with id %s is available in the DB' % replication_id)
        else:
            execution = DimExecution.objects.filter(pk=execid)
            if not execution.exists():
                raise ObjectDoesNotExist("No execution with id %s is available in the DB" % execid)
            replication = execution[0].dimreplication_set.filter(series_id=seriesid)
            if not replication.exists():
                replication = DimReplication(
                    execution_key=execution[0],
                    series_id=seriesid,
                    seed_used=-1
                )
                replication.save()
                self.replication = replication
            else:
                self.replication = replication[0]

        if zip_file is None:
            if msg is None:
                msg = "An error has occurred during the processing of this replication"
            self.set_status(-1, msg)
            return

        input_files = self.unpack_files(zip_file)
        VSRF = input_files['VectorSpeciesReport'] if 'VectorSpeciesReport' in input_files else ''
        DSF = input_files['DemographicsSummary'] if 'DemographicsSummary' in input_files else ''
        ICF = input_files['InsetChart'] if 'InsetChart' in input_files else ''
        BRF = input_files['BinnedReport'] if 'BinnedReport' in input_files else ''

        if not isinstance(VSRF, str):
            raise TypeError('VSRF must be a string containing the file address to the VSRF')
        elif VSRF is not '':
            self.FileList['VectorSpeciesReport'] = VSRF
        if not isinstance(DSF, str):
            raise TypeError('DSF must be a string containing the file address to the DSF')
        elif DSF is not '':
            self.FileList['DemographicsSummary'] = DSF
        if not isinstance(ICF, str):
            raise TypeError('ICF must be a string containing the file address to the ICF')
        elif ICF is not '':
            self.FileList['InsetChart'] = ICF
        if not isinstance(BRF, str):
            raise TypeError('BRF must be a string containing the file address to the BRF')
        elif BRF is not '':
            self.FileList['BinnedReport'] = BRF

        # -------------- Grab the channel listing and other objects needed for the ingester
        # replication = DimReplication.objects.filter(pk=replication_id)
        # if not replication.exists():
        #    raise ObjectDoesNotExist('Replication with id %s does not exist' % replication_id)
        # replication = replication[0]
        self.run = self.replication.execution_key.run_key

        # Attach CSV output for non-sweep runs only
        if self.run.numjobs() == 1:
            convert_to_csv(self.temporary_path)
            filename = os.path.join(self.temporary_path, "output.csv.zip")
            csv_file = SimulationInputFile.objects.create_file(contents=open(filename, "rb").read(),
                                                               name="output.csv.zip",
                                                               created_by_id=1)

            self.run.csv_output = csv_file
            self.run.save()

        if self.run.models_key.model != 'EMOD':
            raise ValueError("Target Run is not EMOD during EMOD submission!")
        if chan_list is not None and isinstance(chan_list, list):
            chans = DimChannel.objects.filter(pk__in=chan_list)
            if not chans.exists():
                raise ObjectDoesNotExist('No channels were found with IDs %s' % chan_list)
            new_chans = [self.run.dimchannel_set.add(channel) for channel in chans]
            if len(new_chans) != len(chans):
                print "WARNING: Not all channels in list were ingested"
            self.run.save()
        else:
            chans = self.run.dimchannel_set.all()

        self.Channel_dict = dict()
        for channel in chans:
            if channel.file_name not in self.Channel_dict:
                self.Channel_dict[channel.file_name] = list()
            self.Channel_dict[channel.file_name].append(channel)
        self.Channel_dict['VectorSpeciesReport'] = list()

        self.alreadyIngested = BaseFactData.objects.filter(
            run_key=self.run,
            replication_key=self.replication
        ).distinct('channel_key')

        self.alreadyIngested = [data.channel_key for data in self.alreadyIngested]
        # self.Channel_list = [x.file_name for x in chans]

        # Setup class variables
        self.fact_data_name = 'fact_data_run_%s' % self.run.id

        self.cursor = connections['default'].cursor()

        self.cursor.execute("select nextval('base_fact_data_id_seq');")
        self.next_id = int(self.cursor.fetchone()[0])
        # Due to the limitations of the django ORM, we have to use psycopg2 directly

    def __del__(self):
        """
        This is the exit method and will cleanup temporary files, even if there is an exception.  This will walk the
        tree of the temporary path, deleting all files and folders therein, and then removing the temporary directory
        itself.
        """
        if self.temporary_path:
            self._cleanupIngester()

    @classmethod
    def rep_failed(cls, execid, seriesid, msg=None):
        """
        This is the pathway for failed replications returning from computation

        If a replication fails, the seriesid and execution id will be passed in to
        this alternate constructor for the ingester.  It will create the appropriate
        replication if it does not exist (it will check for the existence of the
        same replication via checking the seriesid and execution id) and then set
        the status.  It will further set the status text to msg unless msg is empty,
        if it is it will fill the text with a default status string.

        *NOTE* This does not take a zip file

        :param execid: Execution ID of the failed replication
        :param seriesid: Series ID of the failed replication
        :param msg: Status message to set the failed replication to.
        """
        if not isinstance(execid, int) and not isinstance(seriesid, int):
            raise ValueError("Execid and seriesid are required to be integers")

        return cls(
            zip_file=None,
            execid=execid,
            seriesid=seriesid,
            msg=msg
        )

    def ingest(self):
        """ This ingest method will step through all of the files in the file list and
        add the data contained within them to the database.  This method is also the
        "main" for this ingester, and contains byte conversion and the like

        :returns: Nothing
        """
        t1 = datetime.datetime.now()
        # Preprocess
        # self.preProcess()

        # Ready the byte container and add the Postgres Header

        cpy = BytesIO()
        cpy.write(pack('!11sii', b'PGCOPY\n\377\r\n\0', 0, 0))

        for file_type in self.Channel_dict.keys():
            try:
                parser = self.parse_file(str(file_type))
                self.next_id = parser(str(file_type), cpy, self.next_id)
                # self.parse_file(str(file_type), cpy, self.next_id)
            except KeyError as detail:
                self.set_status(-1, "Key error, a key of %s was not found" % detail)
                return

        # Close the file as per postgresql docs
        cpy.write(pack('!h', -1))

        commit_to_warehouse(cpy, connections['default'].settings_dict, 'base_fact_data', self.next_id)
        #cpy.seek(0)
        #conn_dict = connections['default'].settings_dict
        #conn = psycopg2.connect(
        #    host=conn_dict['HOST'],
        #    port=conn_dict['PORT'],
        #    user=conn_dict['USER'],
        #    password=conn_dict['PASSWORD'],
        #    database=conn_dict['NAME'])
        #data_cursor = conn.cursor()
        #data_cursor.copy_expert('COPY base_fact_data FROM STDIN WITH BINARY', cpy)
        #data_cursor.close()
        #conn.commit()
        #conn.close()

        # Reset the sequence counter to the appropriate value
        #cursor.execute('ALTER SEQUENCE base_fact_data_id_seq RESET %s' % next_id)

        # Re-add all constraints
        # TODO: Also include re-adding indexes if they were deleted or creating new ones.

        # self.postProcess()
        t2 = datetime.datetime.now()
        print "Ingestion process took ", t2-t1

        # cleanup the files
        print "Removing the temporary files"
        if self.temporary_path:
            shutil.rmtree(self.temporary_path)

        # Replication and run status update
        self.set_status(0)
        self.run.set_status()

        # print self.run.status
        self.run.save()
        return

    def parse_file(self, file_type):
        """
        This method is responsible for choosing which method to use on which file. This is being used as a replacement
        for the swicth stack.

        This accomplishes this by returning a ByteIO containing the information contained within the file.

        :param file_type: Type of file (ex BRF, ICF, etc)
        :type file_type: str
        :param pg_index: Index in data table to start with
        :type pg_index: int
        :param pg_io: BytesIO object to fill with data from a particular channel
        :type pg_io: BytesIO
        """
        return{
            'VectorSpeciesReport': self.parse_vector_species
        }.get(file_type, self.parse_generic_file)

    def parse_generic_file(self, file_type, pg_io, pg_index):
        """
        This method is responsible for parsing the DemographicsSummary, BinnedReport, and InsetChart files for
        the EMOD model.  It does not parse the VectorSpeciesReport file.

        :param file_type: Type of file (ex BRF, ICF, etc)
        :type file_type: str
        :param pg_index: Index in data table to start with
        :type pg_index: int
        :param pg_io: BytesIO object to fill with data from a particular channel
        :type pg_io: BytesIO
        """
        filename = self.FileList[file_type]

        file_json = json.loads(open(filename, 'r').read())
        channel_list = self.Channel_dict[file_type]
        for chan in channel_list:
            # To ensure that a single channel is never ingested more than once
            if chan in self.alreadyIngested:
                continue
            try:
                if chan.type is not None:
                    type_ndx = file_json['Header']['Subchannel_Metadata']['MeaningPerAxis'][0].index(chan.type)
                    data = file_json['Channels'][chan.title]['Data'][type_ndx]
                else:
                    data = file_json['Channels'][chan.title]['Data']

                pg_index = self.transform_data(data, chan, pg_io, pg_index)
            except KeyError:
                title = chan.title
                if chan.type is not None:
                    title += ' - ' + chan.type
                self.set_status(-1, 'Channel %s not found in output file; Ingestion Failed' % title)
                raise KeyError('Channel %s not found in output file; Ingestion Failed' % title)
        return pg_index

    def parse_vector_species(self, file_type, pg_io, pg_index):
        """
        This method is responsible for parsing the VectorSpecies file.  As all vector species quantities should ingested
        for each run, this file will be completely ingested, and will create channels and add those channels to the
        run if necessary.

        :param file_type: Type of file (ex BRF, ICF, etc)
        :type file_type: str
        :param pg_index: Index in data table to start with
        :type pg_index: int
        :param pg_io: BytesIO object to fill with data from a particular channel
        :type pg_io: BytesIO
        """
        filename = self.FileList[file_type]

        file_obj = open(filename, 'r')
        file_json = json.loads(file_obj.read())
        file_obj.close()

        species_list = file_json['Header']['Subchannel_Metadata']['MeaningPerAxis'][0]
        channels = file_json['Channels'].keys()

        for chan_ndx, chan in enumerate(channels):
            try:
                data_lists = file_json['Channels'][channels[chan_ndx]]['Data']
                for spec_ndx, spec_data in enumerate(data_lists):
                    channel = DimChannel.objects.get_or_create(
                        title=chan,
                        type=species_list[spec_ndx],
                        file_name='VectorSpeciesReport'
                    )
                    channel = channel[0]
                    # To ensure that a single channel is never ingested more than once
                    if channel in self.alreadyIngested:
                        continue
                    self.run.dimchannel_set.add(channel)
                    pg_index = self.transform_data(spec_data, channel, pg_io, pg_index)
            except KeyError:
                title = chan.title
                if chan.type is not None:
                    title += ' - ' + chan.type
                self.set_status(-1, 'Channel %s not found in output file; Ingestion Failed' % title)
                raise KeyError('Channel %s not found in output file; Ingestion Failed' % title)

        self.run.save()
        return pg_index


    def preProcess(self):
        """ This pre-processing method 'turns off' the foreign-key constraints and uniqueness constraints on
        the fact data table being ingested into

        :returns: Nothing
        """

        # Drop Constraints
        self.cursor.execute("select conname from pg_constraint where conname = 'base_fact_data_fk_channel_key'")
        if self.cursor.fetchone() is not None:
            self.cursor.execute('alter table base_fact_data drop constraint base_fact_data_fk_channel_key;')
            transaction.commit_on_success(using='default')
        # cursor.execute('alter table base_fact_data drop constraint base_fact_data_fk_run_key')
        self.cursor.execute("select conname from pg_constraint where conname = '%s_run_key_check';" % self.fact_data_name)
        if self.cursor.fetchone() is not None:
            self.cursor.execute('alter table %(fact_table)s drop constraint %(fact_table)s_run_key_check;' % {'fact_table': self.fact_data_name})
            transaction.commit_on_success(using='default')

        self.cursor.close()
        return

    def postProcess(self):
        """ This is post-processing method restores that constraints that were 'turned off' in pre-processing.
        It then will validate all new data.

        :returns: Nothing
        """
        self.cursor = connections['default'].cursor()

        # Re-create constraints
        self.cursor.execute("select conname from pg_constraint where conname = 'base_fact_data_fk_channel_key'")
        if self.cursor.fetchone() is None:
            query = "ALTER TABLE base_fact_data ADD CONSTRAINT base_fact_data_fk_channel_key FOREIGN KEY (channel_key) REFERENCES dim_channel (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION;"
            self.cursor.execute(query)
            transaction.commit_on_success(using='default')

        # query = """
        # ALTER TABLE base_fact_data ADD CONSTRAINT base_fact_data_fk_run_key FOREIGN KEY (run_key)
        # REFERENCES dim_run (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE NO ACTION
        # """
        # cursor.execute(query)
        #self.conn.commit()
        self.cursor.execute("select conname from pg_constraint where conname = '%s_run_key_check'" % self.fact_data_name)
        if self.cursor.fetchone() is None:
            query = """
            ALTER TABLE %(fact_table)s ADD CONSTRAINT %(fact_table)s_run_key_check CHECK (run_key = %(run_id)s);
            """ % {'fact_table': self.fact_data_name, 'run_id': self.run.id}
            self.cursor.execute(query)
            transaction.commit_on_success(using='default')

        # Validate all constraints
        # cursor.execute('ALTER TABLE base_fact_data VALIDATE CONSTRAINT base_fact_data_fk_channel_key')
        # self.conn.commit()
        # cursor.execute('ALTER TABLE base_fact_data VALIDATE CONSTRAINT base_fact_data_fk_run_key')
        #self.conn.commit()
        # cursor.execute('ALTER TABLE %(fact_table)s VALIDATE CONSTRAINT %(fact_table)s_run_key_check'
        #     % {'fact_table': self.fact_data_name})
        # self.conn.commit()

        return

    def transform_data(self, data, channel, pg_io, pg_index):
        """
        The purpose of this method is to transform the data as a list into a binary data.  Originally it was part of
        each parse_file call, but it was refactored to here.  Not the base_ingester class, as only EMOD currently uses
        this, but the OM ingester could easily be refactored for this.

        :param data: list of data where the index of any given row is its timestep
        :type data: list
        :param channel: Channel that the data should be associated with
        :type channel: DimChannel
        :param pg_io: BytesIO to which to add data
        :type pg_io: BytesIO
        :param pg_index: Index for which the data should be inserted at
        :type pg_index: int
        """
        if not isinstance(data, list):
            raise ValueError('Data must be a list of numbers, received %s', type(data))
        if not isinstance(channel, DimChannel):
            raise ValueError('Channel must be an instance of DimChannel, received %s' % type(channel))
        if not isinstance(pg_io, BytesIO):
            raise ValueError('pg_io must be a BytesIO instance to which the data will be appended, received %s' % type(pg_io))
        if not isinstance(pg_index, int):
            raise ValueError('pg_index must be an integer, received %s' % type(pg_index))

        for ts, datum in enumerate(data):
            pg_io.write(
                encode_binary(
                    pg_id=pg_index,
                    timestep=ts,
                    value=datum,
                    channel_key=channel.id,
                    run_key=self.run.id,
                    replication_key=self.replication.id)
            )
            pg_index += 1

        return pg_index













