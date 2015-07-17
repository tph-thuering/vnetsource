"""
This module contains the tests relevant for the data_service.models
"""


from django.test import TestCase
from data_services.models import *
from django.core.exceptions import ObjectDoesNotExist
from data_services.models import DimRun, DimUser
from data_services.adapters import EMOD_Adapter, OM_Adapter

class DimBinDataTests(TestCase):
    """
    This contains the methods for testing the pg_utils package
    """

    fixtures = ['users.json', 'channels.json']

    def setUp(self):
        """
        This will reset everything required for each test.

        This is run between every test.
        """
        self.dimbinfile = DimBinFiles.objects.create(file_name="config.json",description="File to be used by unittest")

        return

    def test_read(self):
        """
        Testing read
        """
        # Testing read from saved .content field
        self.dimbinfile.content = "Test_read"
        self.dimbinfile.save()
        fp = self.dimbinfile.open()
        self.assertEqual(self.dimbinfile.fp, fp, "File handle returned doesn't match self.fp")
        content = fp.read()
        self.assertEqual(content, "Test_read", "Can't read DimBinFile")

        # Testing read without saving model to the database
        self.dimbinfile.content = "Test_read2"
        content = self.dimbinfile.open().read()
        self.assertEqual(content, "Test_read2", "Can't read content of unsaved DimBinFile")


    def test_write(self):
        """
        Testing write
        """
        self.dimbinfile.open(mode="w").write("TestTest")
        self.dimbinfile.close()
        self.assertEqual(self.dimbinfile.content,
                         "TestTest",
                         "Couldn't write to DimBinFile")

        #
        self.dimbinfile.open(mode="w").write("Test")
        self.dimbinfile.close()
        self.assertEqual(self.dimbinfile.content,
                         "Test",
                         "Second write to DimBinFile failed. 'Test' string expected, '%s' was read"
                         % self.dimbinfile.content
        )

        dimbinfile = DimBinFiles.objects.get(id = self.dimbinfile.id)
        self.assertEqual("Test", dimbinfile.content,
                         "Couldn't write to an object in database. 'Test' string expected, '%s' was read"
                        % self.dimbinfile.content)


    def test_wrong_parameters(self):
        self.assertRaises(RuntimeError, self.dimbinfile.open, "bla")
        self.assertRaises(RuntimeError, self.dimbinfile.open, "a")

class DimRunTests(TestCase):
    """
    This contains the methods for testing the DimRun class
    """

    fixtures = ['location.json', 'models.json', 'templates.json', 'users.json', 'channels.json']

    # def setUp(self):
    #     emod_adapter = EMOD_Adapter("unittest")
    #     template_id = 2
    #     location_ndx = None
    #
    #     START_YEAR = 1900
    #     START_MONTH = 7
    #     START_DAY = 4
    #     start_date = '%04d-%02d-%02d' % (START_YEAR, START_MONTH, START_DAY)
    #
    #     END_YEAR = 1941
    #     END_MONTH = 12
    #     END_DAY = 7
    #     end_date = '%04d-%02d-%02d' % (END_YEAR, END_MONTH, END_DAY)
    #
    #     TIMESTEP_INTERVAL = 5
    #
    #     VERSION_NUMBER = 1.0
    #     RELEASE_NUMBER = 4.75
    #     version = '%f-%f' % (VERSION_NUMBER, RELEASE_NUMBER)
    #
    #     self.run_without_jcd = emod_adapter.save_run(scenario_id, template_id, start_date, "Test run without JCD", "Test Run without JCD",
    #                                                  location_ndx, TIMESTEP_INTERVAL, version, end_date=end_date, as_object=True)
    #     self.run_with_jcd = emod_adapter.save_run(scenario_id, template_id, start_date, "Test run with JCD", "Test Run with JCD, but no sweeps",
    #                                                  location_ndx, TIMESTEP_INTERVAL, version, end_date=end_date, as_object=True)
    #     self.run_with_jcd.set_input_files({"config.json":"1234"})

    def test_set_input_files(self):
        config = '{"param": "1234512345"}'
        campaign = '{"test": "Test campaign file"}'
        self.run_with_jcd.set_input_files({"config.json": config,
                                           "campaign.json":campaign})
        input_files = self.run_with_jcd.get_input_files()
        correct_names = 0
        for input_file, content in input_files.iteritems():
            if input_file == "config.json":
                self.assertEqual(content, config, "")
                correct_names += 1
            if input_file == "campaign.json":
                self.assertEqual(content, campaign, "Campaign.json wasn't saved properly. Expected: %s, got %s" % (campaign, content))
                correct_names += 1
        self.assertEqual(correct_names, 2, "Not all file names are correct")
        self.assertEqual(len(input_files), 2, "Too many files were saved (%s)" % len(input_files))

        pass

    def test_has_sweeps(self):
        self.assertRaises(ValueError, self.run_without_jcd.has_sweeps)
        self.assertFalse(self.run_with_jcd.has_sweeps())
        self.assertIsNone(self.run_with_jcd.get_sweeps())
        #self.assertTrue(self.run_with_sweeps.has_sweeps())

    def test_sweeps(self):

        config = '{"param": "1234512345"}'
        campaign = '{"test": "Test campaign file"}'
        self.run_with_jcd.set_input_files({"config.json": config,
                                           "campaign.json":campaign},
                                          sweeps={"config.json/param1":"1:3:1"})
        #print self.run_with_jcd.jcd
        self.assertTrue(self.run_with_jcd.has_sweeps())
        sweeps = self.run_with_jcd.get_sweeps()
        self.assertIsNotNone(sweeps)
        self.assertEqual(sweeps[0]["config.json/param1"],"1:3:1", "Wrong sweep value: excepted 1:3:1, got %s" % sweeps[0]["config.json/param1"])
        self.assertEqual(len(sweeps),1,"One sweep expected, %s returned" % len(sweeps))
        input_files = self.run_with_jcd.get_input_files()
        correct_names = 0
        for input_file, content in input_files.iteritems():
            if input_file == "config.json":
                self.assertEqual(content, config, "")
                correct_names += 1
            if input_file == "campaign.json":
                self.assertEqual(content, campaign, "Campaign.json wasn't saved properly. Expected: %s, got %s" % (campaign, content))
                correct_names += 1
        self.assertEqual(correct_names, 2, "Not all file names are correct")
        self.assertEqual(len(input_files), 2, "Too many files were saved (%s)" % len(input_files))