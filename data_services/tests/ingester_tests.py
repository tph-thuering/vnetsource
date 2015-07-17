"""
Tests for the ingester modules currently housed in data_services
"""

__author__ = 'lselvy'

#from io import BytesIO
import io
from django.test import TransactionTestCase
from django.db.models import Count
from data_services.adapters import EMOD_Adapter, OM_Adapter
from data_services.models import DimExecution, DimReplication, DimChannel, BaseFactData, DimRun
from data_services.ingesters import EMOD_ingester
from django.db.backends.util import CursorWrapper
from struct import pack
from django.db.models import ObjectDoesNotExist
from django.db import transaction
import hashlib
import os
import pdb

class EmodIngestTest(TransactionTestCase):
    """
    These are the EMOD ingestion tests.
    """

    fixtures = ['location.json', 'models.json', 'templates.json', 'users.json', 'channels.json']
    #multi_db = True

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

    # def setUp(self):
    #     """
    #     This will reset everything in the data warehouse between tests
    #     """
    #     self.data_file = 'data_services/tests/static_files/test-9999.zip'
    #     self.adapter = EMOD_Adapter('admin')
    #     self.anonymous_adapter = EMOD_Adapter()
    #
    #     #------------ Setup the test data stack --------------#
    #     self.run = self.adapter.save_run(
    #         4,
    #         '1986-05-30',
    #         'Test Run',
    #         'Run for testing',
    #         1,
    #         1,
    #         '1.5-2696',
    #         model_id=1,
    #         duration=10000,
    #         as_object=True
    #     )
    #     self.execution = DimExecution(
    #         run_key=self.run,
    #         name='Test Execution',
    #         replications=1,
    #     )
    #     self.execution.save()
    #     self.replication = DimReplication(
    #         id=9999,
    #         seed_used=1,
    #         series_id=1,
    #         execution_key=self.execution
    #     )
    #     self.replication.save()
    #
    #     #zip_file = open(self.data_file, 'r')
    #     #self.ingester = EMOD_ingester(zip_file)
    #     self.ingester = EMOD_ingester(self.data_file)
    #
    #     return

    def test_init(self):
        """
        This tests 'normal' EMOD ingestion.  This would be the case where data was coming from the cluster
        originally to the data warehouse.  The run should have the golden channels associated with it, and
        only those will be ingested.
        """

        print '\nTesting init method of ingester'

        self.assertEqual(
            self.ingester.run,
            self.run,
            msg='An error occurred during run instantiation in the ingester.'
        )

        self.assertEqual(
            self.ingester.replication,
            self.replication,
            msg="An error occurred during replication instantiation in the ingester."
        )

        self.assertEqual(
            os.path.split(self.ingester.FileList['DemographicsSummary'])[-1],
            'DemographicsSummary.json',
            msg="Demographics Summary File path is incorrect.  Expected DemographicsSummary.json, received %s" %
            os.path.split(self.ingester.FileList['DemographicsSummary'])[-1]
        )

        self.assertEqual(
            os.path.split(self.ingester.FileList['InsetChart'])[-1],
            'InsetChart.json',
            msg="Inset Chart File path is incorrect.  Expected InsetChart.json, received %s" %
            os.path.split(self.ingester.FileList['InsetChart'])[-1]
        )

        self.assertEqual(
            os.path.split(self.ingester.FileList['VectorSpeciesReport'])[-1],
            'VectorSpeciesReport.json',
            msg="Vector Species Report File path is incorrect.  Expected VectorSpeciesReport.json, received %s" %
            os.path.split(self.ingester.FileList['VectorSpeciesReport'])[-1]
        )

        self.assertEqual(
            os.path.split(self.ingester.FileList['BinnedReport'])[-1],
            'BinnedReport.json',
            msg="Binned Report File path is incorrect.  Expected BinnedReport.json, received %s" %
            os.path.split(self.ingester.FileList['BinnedReport'])[-1]
        )

        for filename, channels in self.ingester.Channel_dict.iteritems():
            db_chans = DimChannel.objects.filter(
                pk__in=self.golden_channel_list,
                file_name=filename
            )
            self.assertEqual(
                len(db_chans),
                len(channels),
                msg="Number of channels for file type %(filename)s mismatched, expected %(db)s, received %(file)s" %
                    {
                        'filename': filename,
                        'db': len(db_chans),
                        'file': len(channels)
                    }
            )

            for chan in db_chans:
                self.assertIn(
                    chan,
                    channels,
                    msg='Channel %(title)s-%(type)s is missing from ingestion data' %
                        {'title': chan.title, 'type': chan.type}
                )

        self.assertEqual(
            self.ingester.alreadyIngested,
            [],
            msg='Ingester alreadyIngested channels contains channels when should be empty.'
        )

        self.assertEqual(
            self.ingester.fact_data_name,
            'fact_data_run_%s' % self.run.id,
            msg='Fact Data Naming is incorrect, expected %(expect)s received $(actual)' %
                {'expect': 'fact_data_run_%s' % self.run.id, 'actual': self.ingester.fact_data_name}
        )

        self.assertIsInstance(
            self.ingester.cursor,
            CursorWrapper,
            msg="Ingestion cursor not instantiated correctly"
        )

        return

    def test_parse_generic_file(self):
        """
        This will test the parse_generic_file method of the EMOD ingester.

        The main portion of the test will be to examine if a specific BytesIO is created.  We do this by
        first running the method on a set of data we know that works.  We see the output and use the md5
        hashing algorithm.  We save those results and compare against that.
        """
        print "\nTesting generic file parsing"
        expected_index = 65701
        expected_size = 3547819
        file_hash = hashlib.new('md5')
        file_type = 'InsetChart'
        pg_io = io.BytesIO()
        pg_io.write(pack('!11sii', b'PGCOPY\n\377\r\n\0', 0, 0))
        pg_index = 1

        pg_index = self.ingester.parse_generic_file(file_type=file_type, pg_io=pg_io, pg_index=pg_index)
        pg_io.seek(0)

        self.assertEqual(
            pg_index,
            expected_index,
            msg="Returned number of rows is not correct.  Expected %(expected)s received %(received)s" %
                {
                    'expected': expected_index,
                    'received': pg_index
                }
        )

        size = len(pg_io.read())
        self.assertEqual(
            size,
            expected_size,
            msg="Length of returned binary is not correct.  Expected %(expected)s recieved %(received)s" %
                {
                    'expected': expected_size,
                    'received': size
                }
        )

        return

    def test_parse_vector_species(self):
        """
        This will test the parse_vector_species method of the EMOD_ingester.

        This is done by running through the vector species parsing method.  Once finished, we inspect the size
        of the resulting BytesIO and the number of rows generated.  Since we are not gauaranteed order (we are
        parsing from JSON and using a dictionary to do it), this tells us if we have the correct information.
        """
        print "\nTesting vector species parsing"
        expected_index = 43801
        expected_size = 2365219
        pg_io = io.BytesIO()
        pg_io.write(pack('!11sii', b'PGCOPY\n\377\r\n\0', 0, 0))
        pg_index = 1
        file_type = 'VectorSpeciesReport'

        pg_index = self.ingester.parse_vector_species(file_type=file_type, pg_io=pg_io, pg_index=pg_index)
        pg_io.seek(0)

        self.assertEqual(
            pg_index,
            expected_index,
            msg="Returned number of rows is not correct.  Expected %(expected)s received %(received)s" %
                {
                    'expected': expected_index,
                    'received': pg_index
                }
        )

        size = len(pg_io.read())
        self.assertEqual(
            size,
            expected_size,
            msg="Length of returned binary is not correct.  Expected %(expected)s recieved %(received)s" %
                {
                    'expected': expected_size,
                    'received': size
                }
        )

        return

    def test_set_status(self):
        """
        This will test the set status method of the ingester to make sure that the replication's status can be
        updated.
        """
        self.ingester.set_status(0)
        self.replication = DimReplication.objects.get(pk=self.replication.id)

        self.assertEqual(
            self.replication.status,
            0,
            msg="Set status to passed for replication failed"
        )

        self.ingester.set_status(-1, status_msg="Setting failed status for test")
        self.replication = DimReplication.objects.get(pk=self.replication.id)

        self.assertEqual(
            self.replication.status,
            -1,
            msg="Set status to failed for replication failed"
        )

        self.assertEqual(
            self.replication.status_text,
            "Setting failed status for test",
            msg="Setting status message for replication failed"
        )

    def test_ingest(self):
        """
        This will test the ingest method of the EMOD ingester.

        This stands as both a unit test for the connection and copy of the binary data as well as a functional test.
        """
        print "\nTesting ingest"

        # ---------- Due to how django sets up its test database, the working behind sharding out based on run is
        # ---------- not functional.  So we are going to use the fact_data table instead.  In this way we can still
        # ---------- run ingestion tests in the django unit test framework.
        self.ingester.fact_data_name = 'fact_data'
        self.ingester.ingest()
        values_per_channel = 10950

        channels = BaseFactData.objects.filter(
            run_key=self.run.id,
            replication_key=self.replication.id
        ).values('channel_key').annotate(Count('value'))

        self.assertEqual(
            len(channels),
            20,
            msg="Expected 20 channels, received %s, ingestion failed." % len(channels)
        )

        for result in channels:
            self.assertEqual(
                result['value__count'],
                values_per_channel,
                msg="Expected %(value)s for channel %(channel)s, received %(result)s" %
                    {
                        'value': values_per_channel,
                        'channel': result['channel_key'],
                        'result': result['value__count']
                    }
            )

        self.replication = DimReplication.objects.get(pk=self.replication.id)
        self.assertEqual(
            self.replication.status,
            0,
            msg="Setting replication after successful ingestion failed."
        )
        return

    def test_bad_simulation_ingest(self):
        """
        This tests to make sure when a bad simulation type is ingested that the ingester fails gracefully.

        To do this we ingest a prepared file with a bad simulation type listed.  This will try to ingest channels
        that do not exist in the output, and fail.  It will then update the replication.
        """
        print "\nTesting bad sim type ingestion"

        # ---------- Due to how django sets up its test database, the working behind sharding out based on run is
        # ---------- not functional.  So we are going to use the fact_data table instead.  In this way we can still
        # ---------- run ingestion tests in the django unit test framework.
        self.ingester.fact_data_name = 'fact_data'
        data_file = 'data_services/tests/static_files/badSimType-9999.zip'
        #data_file = open(data_file, 'r')
        ingester = EMOD_ingester(data_file)
        ingester.ingest()

        self.replication = DimReplication.objects.get(pk=self.replication.id)

        self.assertEqual(
            self.replication.status,
            -1,
            msg="Failed ingestion failed to set replication status."
        )

        row_count = BaseFactData.objects.all().aggregate(Count('value'))

        self.assertEqual(
            row_count['value__count'],
            0,
            msg="Rows were detected, no rows were expected.  Ingestion failed."
        )
        return


