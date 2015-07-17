"""
Here we test the functionality of the baseline object, including its ability to save files to a
test data warehouse.
"""

import os
import tempfile
import random
import string
import hashlib
from django.test import TestCase
from data_services.data_api import EMODBaseline, get_baseline
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from data_services.models import DimModel, DimBinFiles, DimUser, DimBaseline, DimLocation


class GetBaseline(TestCase):
    """
    Here we test whether the factory function can handle the common typos associated with EMOD
    """

    fixtures = ['models.json']

    def test_get_baseline(self):
        """
        We instantiate several EMOD Baselines, making sure that it can be instantiated, each time
        creating the EMOD Baseline object using the factory method
        """
        common_emod_spellings = [
            'EMOD',
            'emod'
        ]

        for model in common_emod_spellings:
            baseline = get_baseline(model)()
            self.assertIsInstance(
                baseline,
                EMODBaseline,
                msg="An EMOD Baseline was not created for common spelling %s" % model
            )

    def test_get_baseline_bad_model(self):
        """
        This will test to make sure the get_baseline method will throw the appropriate NotImplemented Exception
        """
        self.assertRaises(
            NotImplementedError,
            get_baseline,
            'NotAModel'
        )

class BaselineInitAdd(TestCase):
    """
    Here we test the initialization and add file functionality.
    """

    fixtures = ['models.json', 'users.json', 'location.json']

    #def setUp(self):
    #    """
    #    This is the setup for the test
    #    """

    def test_init(self):
        """
        Here we test to make sure all of the class variables are properly created and initialized
        """
        baseline = EMODBaseline()
        class_vars = [
            ('files', list),
            ('required_filetypes', list),
            ('dimbaseline', None),
            ('id', None),
            ('_name', None),
            ('_description', None),
            ('_is_public', None),
            ('_last_edited', None),
            ('_is_completed', None),
            ('location', None),
            ('model', DimModel)
        ]

        for variable in class_vars:
            self.assertTrue(
                hasattr(baseline, variable[0]),
                msg="Class variable '%s' was not instantiated" % variable[0]
            )

            if variable[1] is not None:
                self.assertIsInstance(
                    getattr(baseline, variable[0]),
                    variable[1],
                    msg="Class variable '%s' should be of type %s, instead it is %s" % (
                        variable[0],
                        variable[1],
                        type(getattr(baseline, variable[0]))
                    )
                )
            else:
                self.assertIs(
                    getattr(baseline, variable[0]),
                    None,
                    msg="Class variable '%s' is not None, should be None" % variable[0]
                )

        self.assertEqual(
            baseline.model.model,
            'EMOD',
            msg="Emod model and scenario model are not the same"
        )

    def test_failed_init(self):
        """
        Here we make sure that if we pass in something to model or user that are not instances of those models
        that we do indeed get the ValueError described
        """
        
        baseline = EMODBaseline(
            name='Testing Good Baseline',
            description='Testing Good Baseline',
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )
        
        self.assertEqual(
            baseline._name,
            'Testing Good Baseline',
            msg="Good scenario failed to create properly, name was not set correctly"
        )
        
        self.assertEqual(
            baseline._description,
            'Testing Good Baseline',
            msg="Good scenario failed to create properly, description was not set correctly"
        )
        
        self.assertEqual(
            baseline.model,
            DimModel.objects.get(pk=1),
            msg="Good scenario failed to create properly, model was not set correctly"
        )
        
        self.assertEqual(
            baseline.user,
            DimUser.objects.get(pk=1),
            msg="Good scenario failed to create properly, user was not set correctly"
        )

        self.assertRaises(
            ValueError,
            EMODBaseline,
            name="Testing Bad Baseline",
            description="Testing Bad Baseline",
            model="EMOD",
            user="Test"
        )

        # Now we test to make sure created user and models fail appropriately
        bad_model = DimModel(model='bad model')

        self.assertRaisesMessage(
            ValueError,
            "model Must be a saved DimModel instance",
            EMODBaseline,
            name="Testing Bad Model",
            description="Testing Bad Model",
            user=DimUser.objects.get(pk=1),
            model=bad_model
        )

        bad_user = DimUser(username='bad user')
        self.assertRaisesMessage(
            ValueError,
            "user Must be a saved DimUser instance",
            EMODBaseline,
            name="Testing Bad User",
            description="Testing Bad User",
            model=DimModel.objects.get(pk=1),
            user=bad_user
        )

    def test_baseline_from_dw(self):
        """
        Here we test if we can fetch a scenario from the data warehouse.
        """
        baseline = EMODBaseline()
        baseline._name = "Testing from_dw"
        baseline._description = "Testing from_dw alternate constructor"
        baseline.model = DimModel.objects.get(pk=1)
        baseline.user = DimUser.objects.get(pk=1)
        baseline.save()

        orig_id = baseline.id

        new_baseline = EMODBaseline.from_dw(pk=orig_id)

        self.assertIsInstance(
            new_baseline,
            EMODBaseline,
            msg="Baseline created was not an EMOD Baseline"
        )

        self.assertEqual(
            new_baseline._name,
            baseline._name,
            msg="Baseline was not fetched correctly"
        )

        self.assertEqual(
            new_baseline.id,
            baseline.id,
            msg="Baseline was not fetched correctly"
        )

    def test_from_dw_excpetions(self):
        """
        Here we test to make sure the appropriate messages are raised when an exception has occurred during the
        from dw call.
        """

        self.assertRaises(
            ObjectDoesNotExist,
            EMODBaseline.from_dw,
            name='This name does not exist'
        )

        b1 = EMODBaseline(
            name='Testing from_dw',
            description="testing failure methods",
            user=DimUser.objects.get(pk=1),
            model=DimModel.objects.get(pk=1)
        )

        b2 = EMODBaseline(
            name='Testing from_dw 2',
            description="testing failure methods 2",
            user=DimUser.objects.get(pk=1),
            model=DimModel.objects.get(pk=1)
        )

        b1.save()
        b2.save()

        self.assertRaises(
            MultipleObjectsReturned,
            EMODBaseline.from_dw,
            model=DimModel.objects.get(pk=1)
        )

    def test_baseline_from_files(self):
        """
        Here we test to see if we can create a scenario from a list of files
        """
        f, path = tempfile.mkstemp()
        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
        os.write(f, rand_str)
        os.close(f)

        flist = [
            {
                'name': 'config',
                'file_type': 'config',
                'path': path
            }
        ]

        baseline = EMODBaseline.from_files(
            flist,
            name="Testing from files",
            description="Testing from files",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        self.assertEqual(
            len(baseline.files),
            1,
            msg="Files were not added appropriately"
        )

        self.assertEqual(
            baseline._name,
            "Testing from files",
            msg="Baseline was not created properly, name was set incorrectly"
        )

        self.assertEqual(
            baseline._description,
            "Testing from files",
            msg="Baseline was not created properly, description was set incorrectly"
        )

        self.assertEqual(
            baseline.model,
            DimModel.objects.get(pk=1),
            msg="Baseline was not created properly, model was set incorrectly"
        )

        self.assertEqual(
            baseline.user,
            DimUser.objects.get(pk=1),
            msg="Baseline was not created properly, user was set incorrectly"
        )

    def test_add_file(self):
        """
        We test to make sure add file properly attaches the file to the object *NOT SAVING IT* and
        we test to make sure that we raise exceptions when needed.  We do this by creating a file,
        filling it with something, and sending it in to the add_file_test.
        """
        baseline = EMODBaseline(
            name="Testing add_file",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )
        file_types = [
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

        self.assertEqual(file_types, baseline.required_filetypes)

        file_count = 0
        for ftype in file_types:
            if 'binary' in ftype:
                name = '%s.bin' % ftype.split(' ')[0]
            elif 'json' in ftype:
                name = '%s.bin.json' % ftype.split(' ')[0]
            else:
                name = '%s.json' % ftype

            f, path = tempfile.mkstemp()

            rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

            os.write(f, rand_str)
            os.close(f)

            added = baseline.add_file(ftype, path, name=name, description='test test')
            file_count += 1

            self.assertTrue(
                added,
                msg="File '%s' was not added" % ftype
            )
            self.assertEqual(
                file_count,
                len(baseline.files),
                msg="There are discrepancies between the number of files added (%s), and the number of files "
                    "that exist (%s)" % (file_count, len(baseline.files))
            )
            file_in = any(filter(lambda x: x['type'] == ftype, baseline.files))

            self.assertTrue(
                file_in,
                msg="File %s was reported as added, but it was not added to local file storage" % ftype
            )

            os.remove(path)

        f, path = tempfile.mkstemp()

        os.close(f)

        self.assertRaises(
            ValueError,
            baseline.add_file,
            'air json', path
        )

        os.remove(path)

        self.assertRaises(
            ValueError,
            baseline.add_file,
            'air_json', path
        )

    def test_add_file_from_string(self):
        """
        This tests adding a file from string instead of by path
        """
        baseline = EMODBaseline(
            name="Testing add_file_from_string",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )
        file_types = [
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

        self.assertEqual(file_types, baseline.required_filetypes)

        file_count = 0
        for ftype in file_types:
            if 'binary' in ftype:
                name = '%s.bin' % ftype.split(' ')[0]
            elif 'json' in ftype:
                name = '%s.bin.json' % ftype.split(' ')[0]
            else:
                name = '%s.json' % ftype

            rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

            added = baseline.add_file_from_string(ftype, name, rand_str, description='test test')
            file_count += 1

            self.assertTrue(
                added,
                msg="File '%s' was not added" % ftype
            )
            self.assertEqual(
                file_count,
                len(baseline.files),
                msg="There are discrepancies between the number of files added (%s), and the number of files "
                    "that exist (%s)" % (file_count, len(baseline.files))
            )
            file_in = any(filter(lambda x: x['type'] == ftype, baseline.files))

            self.assertTrue(
                file_in,
                msg="File %s was reported as added, but it was not added to local file storage" % ftype
            )

    def test_add_binfile(self):
        """
        Tests the add_binfile method functionality and failures
        """
        baseline = EMODBaseline(
            name="Test add binfile",
            description="Adding Binfile Test",
            user=DimUser.objects.get(pk=1),
            model=DimModel.objects.get(pk=1)
        )

        dbf = DimBinFiles(
            file_name="Test for add binfile",
            description="Testing for add binfile method on scenario class",
            file_hash="Some hash",
            file_type="config"
        )

        dbf.save()

        try:
            baseline.add_binfile(dbf)
            self.assertTrue(False, msg="Added binfile to unsaved scenario")
        except ValueError as err:
            self.assertEqual(
                "Baseline must be saved before appending Data Warehouse Bin Files",
                str(err),
                msg="Failed to raise correct exception, expected base save error, found %s" % str(err)
            )

        baseline.save()

        self.assertRaises(
            TypeError,
            baseline.add_binfile,
            5.9
        )

        self.assertRaises(
            TypeError,
            baseline.add_binfile,
            []
        )

        self.assertRaises(
            TypeError,
            baseline.add_binfile,
            {}
        )

        self.assertRaises(
            TypeError,
            baseline.add_binfile,
            '5'
        )

        self.assertRaises(
            ObjectDoesNotExist,
            baseline.add_binfile,
            1000000
        )

        bad_dbf = DimBinFiles(
            file_name="Test for add binfile - bad_file",
            description="Testing for add binfile method on scenario class bad_file",
            file_hash="Some hash bad",
            file_type="config"
        )

        self.assertRaises(
            ValueError,
            baseline.add_binfile,
            bad_dbf
        )

        self.assertEqual(
            len(baseline.files),
            0,
            msg="Expected 0 files, found %s" % len(baseline.files)
        )

        added = baseline.add_binfile(dbf)

        self.assertTrue(
            added,
            msg="Failed to add binfile to scenario"
        )

        self.assertTrue(
            any(map(lambda x: x['id'] == dbf.id, baseline.files)),
            msg="File reported in file list by method result, but is absent"
        )

        baseline = EMODBaseline(
            name="Test add binfile2",
            description="Adding Binfile Test2",
            user=DimUser.objects.get(pk=1),
            model=DimModel.objects.get(pk=1)
        )

        baseline.save()

        added = baseline.add_binfile(dbf.id)

        self.assertTrue(
            added,
            msg="Failed to add binfile to scenario"
        )

        self.assertTrue(
            any(map(lambda x: x['id'] == dbf.id, baseline.files)),
            msg="File reported in file list by method result, but is absent"
        )

    def test_add_air_files(self):
        """
        This tests if the convenience function 'add_air_file' functions properly
        """
        baseline = EMODBaseline(
            name="Testing add_air_files",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        f, path = tempfile.mkstemp()

        os.close(f)

        self.assertRaises(
            ValueError,
            baseline.add_air_file,
            path
        )

        os.remove(path)

        self.assertRaises(
            ValueError,
            baseline.add_air_file,
            path
        )

        f, path = tempfile.mkstemp()

        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

        os.write(f, rand_str)
        os.close(f)

        baseline.add_air_file(path, description="Stuff", name="air json", jsonfile=True)

        self.assertEqual(
            len(baseline.files),
            1,
            msg="Expected 1 file attached to scenario, found %s" % len(baseline.files)
        )

        jsonfile = filter(lambda x: x['type'] == 'air json', baseline.files)
        self.assertEqual(
            len(jsonfile),
            1,
            msg="Expected 1 'air json' file, found %s" % len(jsonfile)
        )

        self.assertEqual(
            jsonfile[0]['type'],
            'air json',
            msg="Incorrect type for 'air json' file, found %s" % jsonfile[0]['type']
        )

        self.assertEqual(
            jsonfile[0]['name'],
            'air json',
            msg="Expected air json file name 'air json', found %s" % jsonfile[0]['name']
        )

        self.assertEqual(
            jsonfile[0]['description'],
            'Stuff',
            msg="Description for air json file incorrect"
        )
        
        self.assertIsNotNone(
            jsonfile[0]['id'],
            msg="JSON file was not saved"
        )
        
        os.remove(path)

        f, path = tempfile.mkstemp()

        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

        os.write(f, rand_str)
        os.close(f)
        
        baseline.add_air_file(path, description="Stuff", name='air binary', jsonfile=False)

        self.assertEqual(
            len(baseline.files),
            2,
            msg="Expected 2 file attached to scenario, found %s" % len(baseline.files)
        )

        jsonfile = filter(lambda x: x['type'] == 'air binary', baseline.files)
        self.assertEqual(
            len(jsonfile),
            1,
            msg="Expected 1 'air binary' file, found %s" % len(jsonfile)
        )

        self.assertEqual(
            jsonfile[0]['type'],
            'air binary',
            msg="Incorrect type for 'air binary' file, found %s" % jsonfile[0]['type']
        )

        self.assertEqual(
            jsonfile[0]['name'],
            'air binary',
            msg="Expected air bin file name 'air binary', found %s" % jsonfile[0]['name']
        )

        self.assertEqual(
            jsonfile[0]['description'],
            'Stuff',
            msg="Description for air bin file incorrect"
        )
        
        self.assertIsNotNone(
            jsonfile[0]['id'],
            msg="JSON Binary was not saved"
        )
        
        os.remove(path)
        
    def test_add_humidity_files(self):
        """
        This tests if the convenience function 'add_humidity_file' functions properly
        """
        baseline = EMODBaseline(
            name="Testing add_humidity_files",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        f, path = tempfile.mkstemp()

        os.close(f)

        self.assertRaises(
            ValueError,
            baseline.add_humidity_file,
            path
        )

        os.remove(path)

        self.assertRaises(
            ValueError,
            baseline.add_humidity_file,
            path
        )

        f, path = tempfile.mkstemp()

        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

        os.write(f, rand_str)
        os.close(f)

        baseline.add_humidity_file(path, description="Stuff", name="humidity json", jsonfile=True)

        self.assertEqual(
            len(baseline.files),
            1,
            msg="Expected 1 file attached to scenario, found %s" % len(baseline.files)
        )

        jsonfile = filter(lambda x: x['type'] == 'humidity json', baseline.files)
        self.assertEqual(
            len(jsonfile),
            1,
            msg="Expected 1 'humidity json' file, found %s" % len(jsonfile)
        )

        self.assertEqual(
            jsonfile[0]['type'],
            'humidity json',
            msg="Incorrect type for 'humidity json' file, found %s" % jsonfile[0]['type']
        )

        self.assertEqual(
            jsonfile[0]['name'],
            'humidity json',
            msg="Expected humidity json file name 'humidity json', found %s" % jsonfile[0]['name']
        )

        self.assertEqual(
            jsonfile[0]['description'],
            'Stuff',
            msg="Description for humidity json file incorrect"
        )
        
        self.assertIsNotNone(
            jsonfile[0]['id'],
            msg="JSON file was not saved"
        )
        
        os.remove(path)

        f, path = tempfile.mkstemp()

        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

        os.write(f, rand_str)
        os.close(f)
        
        baseline.add_humidity_file(path, description="Stuff", name='humidity binary', jsonfile=False)

        self.assertEqual(
            len(baseline.files),
            2,
            msg="Expected 2 file attached to scenario, found %s" % len(baseline.files)
        )

        jsonfile = filter(lambda x: x['type'] == 'humidity binary', baseline.files)
        self.assertEqual(
            len(jsonfile),
            1,
            msg="Expected 1 'humidity binary' file, found %s" % len(jsonfile)
        )

        self.assertEqual(
            jsonfile[0]['type'],
            'humidity binary',
            msg="Incorrect type for 'humidity binary' file, found %s" % jsonfile[0]['type']
        )

        self.assertEqual(
            jsonfile[0]['name'],
            'humidity binary',
            msg="Expected humidity bin file name 'humidity binary', found %s" % jsonfile[0]['name']
        )

        self.assertEqual(
            jsonfile[0]['description'],
            'Stuff',
            msg="Description for humidity bin file incorrect"
        )
        
        self.assertIsNotNone(
            jsonfile[0]['id'],
            msg="JSON Binary was not saved"
        )
        
        os.remove(path)
        
    def test_add_land_temp_files(self):
        """
        This tests if the convenience function 'add_land_temp_file' functions properly
        """
        baseline = EMODBaseline(
            name="Testing add_land_temp",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        f, path = tempfile.mkstemp()

        os.close(f)

        self.assertRaises(
            ValueError,
            baseline.add_land_temp_file,
            path
        )

        os.remove(path)

        self.assertRaises(
            ValueError,
            baseline.add_land_temp_file,
            path
        )

        f, path = tempfile.mkstemp()

        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

        os.write(f, rand_str)
        os.close(f)

        baseline.add_land_temp_file(path, description="Stuff", name="land_temp json", jsonfile=True)

        self.assertEqual(
            len(baseline.files),
            1,
            msg="Expected 1 file attached to scenario, found %s" % len(baseline.files)
        )

        jsonfile = filter(lambda x: x['type'] == 'land_temp json', baseline.files)
        self.assertEqual(
            len(jsonfile),
            1,
            msg="Expected 1 'land_temp json' file, found %s" % len(jsonfile)
        )

        self.assertEqual(
            jsonfile[0]['type'],
            'land_temp json',
            msg="Incorrect type for 'land_temp json' file, found %s" % jsonfile[0]['type']
        )

        self.assertEqual(
            jsonfile[0]['name'],
            'land_temp json',
            msg="Expected land_temp json file name 'land_temp json', found %s" % jsonfile[0]['name']
        )

        self.assertEqual(
            jsonfile[0]['description'],
            'Stuff',
            msg="Description for land_temp json file incorrect"
        )
        
        self.assertIsNotNone(
            jsonfile[0]['id'],
            msg="JSON file was not saved"
        )
        
        os.remove(path)

        f, path = tempfile.mkstemp()

        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

        os.write(f, rand_str)
        os.close(f)
        
        baseline.add_land_temp_file(path, description="Stuff", name='land_temp binary', jsonfile=False)

        self.assertEqual(
            len(baseline.files),
            2,
            msg="Expected 2 file attached to scenario, found %s" % len(baseline.files)
        )

        jsonfile = filter(lambda x: x['type'] == 'land_temp binary', baseline.files)
        self.assertEqual(
            len(jsonfile),
            1,
            msg="Expected 1 'land_temp binary' file, found %s" % len(jsonfile)
        )

        self.assertEqual(
            jsonfile[0]['type'],
            'land_temp binary',
            msg="Incorrect type for 'land_temp binary' file, found %s" % jsonfile[0]['type']
        )

        self.assertEqual(
            jsonfile[0]['name'],
            'land_temp binary',
            msg="Expected land_temp bin file name 'land_temp binary', found %s" % jsonfile[0]['name']
        )

        self.assertEqual(
            jsonfile[0]['description'],
            'Stuff',
            msg="Description for land_temp bin file incorrect"
        )
        
        self.assertIsNotNone(
            jsonfile[0]['id'],
            msg="JSON Binary file was not saved"
        )
        
        os.remove(path)
        
    def test_add_rainfall_files(self):
        """
        This tests if the convenience function 'add_rainfall_file' functions properly
        """
        baseline = EMODBaseline(
            name="Testing add_rainfall_files",
            user=DimUser.objects.get(pk=1),
            model=DimModel.objects.get(pk=1)
        )

        f, path = tempfile.mkstemp()

        os.close(f)

        self.assertRaises(
            ValueError,
            baseline.add_rainfall_file,
            path
        )

        os.remove(path)

        self.assertRaises(
            ValueError,
            baseline.add_rainfall_file,
            path
        )

        f, path = tempfile.mkstemp()

        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

        os.write(f, rand_str)
        os.close(f)

        baseline.add_rainfall_file(path, description="Stuff", name="rainfall json", jsonfile=True)

        self.assertEqual(
            len(baseline.files),
            1,
            msg="Expected 1 file attached to scenario, found %s" % len(baseline.files)
        )

        jsonfile = filter(lambda x: x['type'] == 'rainfall json', baseline.files)
        self.assertEqual(
            len(jsonfile),
            1,
            msg="Expected 1 'rainfall json' file, found %s" % len(jsonfile)
        )

        self.assertEqual(
            jsonfile[0]['type'],
            'rainfall json',
            msg="Incorrect type for 'rainfall json' file, found %s" % jsonfile[0]['type']
        )

        self.assertEqual(
            jsonfile[0]['name'],
            'rainfall json',
            msg="Expected rainfall json file name 'rainfall json', found %s" % jsonfile[0]['name']
        )

        self.assertEqual(
            jsonfile[0]['description'],
            'Stuff',
            msg="Description for rainfall json file incorrect"
        )
        
        self.assertIsNotNone(
            jsonfile[0]['id'],
            msg="JSON file has not been saved"
        )
        
        os.remove(path)

        f, path = tempfile.mkstemp()

        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

        os.write(f, rand_str)
        os.close(f)

        baseline.add_rainfall_file(path, description="Stuff", name='rainfall binary', jsonfile=False)

        self.assertEqual(
            len(baseline.files),
            2,
            msg="Expected 2 file attached to scenario, found %s" % len(baseline.files)
        )

        jsonfile = filter(lambda x: x['type'] == 'rainfall binary', baseline.files)
        self.assertEqual(
            len(jsonfile),
            1,
            msg="Expected 1 'rainfall binary' file, found %s" % len(jsonfile)
        )

        self.assertEqual(
            jsonfile[0]['type'],
            'rainfall binary',
            msg="Incorrect type for 'rainfall binary' file, found %s" % jsonfile[0]['type']
        )

        self.assertEqual(
            jsonfile[0]['name'],
            'rainfall binary',
            msg="Expected rainfall bin file name 'rainfall binary', found %s" % jsonfile[0]['name']
        )

        self.assertEqual(
            jsonfile[0]['description'],
            'Stuff',
            msg="Description for rainfall bin file incorrect"
        )
        
        self.assertIsNotNone(
            jsonfile[0]['id'],
            msg="JSON Binary was not saved"
        )
        
        os.remove(path)

    def test_should_set_name_until_complete_and_valid(self):
        """
        Here we ensure that we can set a name for a scenario up to the point it is both complete and valid.  After that
        point an Error should be returned.
        """

        sname = "Testing Name Orig"
        baseline = EMODBaseline(
            name=sname,
            description="Testing Name setting procedure",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        self.assertEqual(
            baseline.name,
            sname,
            msg="Did not set name correctly, expected '%s', received %s" % (sname, baseline.name)
        )

        sname = "Testing Name 1"
        baseline.name = sname

        self.assertEqual(
            baseline.name,
            sname,
            msg="Did not set name when model was incomplete and invalid, expected '%s', received %s" %
                (sname, baseline.name)
        )

        # Now we make the scenario complete and test if naming works appropriately
        fdict = dict()
        for rf in baseline.required_filetypes:
            f, path = tempfile.mkstemp()
            rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
            os.write(f, rand_str)
            os.close(f)
            m = hashlib.md5()
            m.update(rand_str)
            fhash = m.hexdigest()
            fdict[rf] = {'handle': f, 'path': path, 'hash': fhash}
            baseline.add_file(rf, path, name=rf, description='Testing %s type' % rf)

        baseline.save()

        self.assertTrue(
            baseline.has_required_files,
            msg="Baseline is stating it is incomplete when it is"
        )

        sname = "Testing Name after complete"
        baseline.name = sname

        self.assertEqual(
            baseline.name,
            sname,
            msg="Did not set name after model is complete but not valid, expected '%s', received %s" %
                (sname, baseline.name)
        )

        baseline.is_approved = True

        baseline.save()

        self.assertTrue(
            baseline.is_approved,
            msg="Baseline reporting invalid when it is"
        )

        sname_after = "Testing Name after complete AND valid"
        with self.assertRaises(ValueError):
            baseline.name = sname_after

        self.assertNotEqual(
            baseline.name,
            sname_after,
            msg="Set name after valid and complete, did not expect '%s'" % sname_after
        )

        self.assertEqual(
            baseline.name,
            sname,
            msg="Name should not have been changed, expected '%s', received %s" % (sname, baseline.name)
        )

    def test_should_only_accept_strings(self):
        """
        Here we ensure that only strings (and unicode)are accepted into the scenario.name property, eliciting
        TypeError for other data types.
        """
        baseline = EMODBaseline(
            name="Testing name types",
            description="Testing name types",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        with self.assertRaises(TypeError):
            baseline.name = 5

        with self.assertRaises(TypeError):
            baseline.name = {}

        with self.assertRaises(TypeError):
            baseline.name = []

        with self.assertRaises(TypeError):
            baseline.name = ()

        sname = "Test unicode"
        baseline.name = unicode(sname)

        self.assertEqual(
            baseline.name,
            sname,
            msg="Expected name to be set to '%s', receieved %s" % (sname, baseline.name)
        )

        sname = "Test String"
        baseline.name = sname

        self.assertEqual(
            baseline.name,
            sname,
            msg="Expected name to set to '%s', received %s" % (sname, baseline.name)
        )

    def test_should_update_location_upon_save(self):
        """
        A bug has been reported that the Baseline object does not update location upon save.  The DimBaseline object
        is updated, but the Baseline instance is not.

        Correct behavior is all aspects of a DimBaseline object are updated upon save.
        """
        baseline = EMODBaseline(
            name="Testing location update",
            description="Testing location update upon save",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        baseline.save()

        self.assertIsNone(
            baseline.location,
            msg="Expected scenario location to be none, found %s" % type(baseline.location)
        )

        loc1 = DimLocation.objects.get(pk=1)
        baseline.location = loc1

        self.assertIsNotNone(
            baseline.location,
            msg="Expected location to be set locally, found None"
        )

        self.assertEqual(
            baseline.location,
            loc1,
            msg="Expected location with id %s to be set locally, found %s" % (loc1.id, baseline.location.id)
        )

        # import pdb; pdb.set_trace()
        baseline.save()

        self.assertIsNotNone(
            baseline.location,
            msg="Expected location to be set after save, found None"
        )

        self.assertIsNotNone(
            baseline.dimbaseline.location,
            msg="Expected location to be set after save on dimbaseline object, found None"
        )

        self.assertEqual(
            baseline.location,
            loc1,
            msg="Expected location with id %s after save, found %s" % (loc1.id, baseline.location.id)
        )

        self.assertEqual(
            baseline.dimbaseline.location,
            loc1,
            msg="Expected location with id %s after save on dimbaseline object, found %s" %
                (loc1.id, baseline.location.id)
        )

    def test_should_be_able_to_identify_saved_state(self):
        """
        Here we test the Baseline's ability to detect if it has been saved (a data warehouse object is present) or
        if it is to be saved.
        """

        baseline = EMODBaseline(
            name="Testing save detection",
            description="Testing save detection",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        self.assertFalse(
            baseline.is_saved,
            msg="Baseline has not been saved, but it is reporting that it is saved"
        )

        baseline.save()

        self.assertTrue(
            baseline.is_saved,
            msg="Baseline is saved, but reporting that it has not been saved"
        )

        with self.assertRaises(AttributeError):
            baseline.is_saved = True

    def test_description_should_only_allow_strings(self):
        """
        Here we verify that the description can only be set to strings or unicode values
        """
        sdesc = "desc1"
        baseline = EMODBaseline(
            name="Testing description setting - types",
            description=sdesc,
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        self.assertEqual(
            baseline.description,
            sdesc,
            msg="Description was not set when given a string"
        )

        baseline.description = unicode(sdesc)

        self.assertEqual(
            baseline.description,
            sdesc,
            msg="Description was not set when given unicode"
        )

        with self.assertRaises(TypeError):
            baseline.description = 5

        with self.assertRaises(TypeError):
            baseline.description = {}

        with self.assertRaises(TypeError):
            baseline.description = []

        with self.assertRaises(TypeError):
            baseline.description = ()

    def test_should_allow_setting_of_description_always(self):
        """
        Here we test to make sure that every description can be saved (as long as it is a string).  Since description
        does not contribute to the uniqueness of a scenario, it can be altered without entering into the versioning
        system.
        """
        sdesc = "desc1"
        baseline = EMODBaseline(
            name="Testing description setting",
            description=sdesc,
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        self.assertEqual(
            baseline.description,
            sdesc,
            msg="Description was not set on scenario before complete and before save"
        )

        baseline.save()

        self.assertEqual(
            baseline.description,
            sdesc,
            msg="Description was not set on scenario before complete and after save"
        )

        self.assertEqual(
            baseline.dimbaseline.description,
            sdesc,
            msg="Description was not set on dimbaseline object"
        )

        sdesc = "desc after save"
        baseline.description = sdesc
        self.assertEqual(
            baseline.description,
            sdesc,
            msg="Description not set after change after save"
        )

        self.assertEqual(
            baseline.dimbaseline.description,
            sdesc,
            msg="Description not set on dimbaseline after change after save"
        )

        # Now we make the scenario complete and test if naming works appropriately
        fdict = dict()
        for rf in baseline.required_filetypes:
            f, path = tempfile.mkstemp()
            rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
            os.write(f, rand_str)
            os.close(f)
            m = hashlib.md5()
            m.update(rand_str)
            fhash = m.hexdigest()
            fdict[rf] = {'handle': f, 'path': path, 'hash': fhash}
            baseline.add_file(rf, path, name=rf, description='Testing %s type' % rf)

        self.assertTrue(
            baseline.has_required_files,
            msg="Baseline is reporting incomplete when it is"
        )
        sdesc = "desc2"
        baseline.description = sdesc

        self.assertEqual(
            baseline.description,
            sdesc,
            msg="Description was not set on scenario after complete"
        )

        baseline.is_approved = True

        self.assertTrue(
            baseline.is_approved,
            msg="Baseline was not approved"
        )

        sdesc = "desc3"
        baseline.description = sdesc
        self.assertEqual(
            baseline.description,
            sdesc,
            msg="Description was not set on scenario after complete and valid"
        )


class BaselineSaveAndHelpers(TestCase):
    """
    In this test suite, we test the save functionality of the scenario object, making sure that both the DimBaseline
    object is updated appropriately as well as the DimBinFiles objects.  We also make sure all of the helper functions
    that describe the completeness of the scenario also function completely.
    """

    fixtures = ['models.json', 'users.json']

    def test_delete(self):
        """
        Here we test to see if the soft delete works
        """
        baseline1 = EMODBaseline(
            name="Testing delete",
            description="Testing delete",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )
        baseline1.save()

        baseline2 = EMODBaseline(
            name="Testing delete 2",
            description="Testing delete 2",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )
        baseline2.save()

        baselines = EMODBaseline.list_baselines(
            DimUser.objects.get(pk=1)
        )

        self.assertEqual(
            len(baselines),
            2,
            msg="Expected 2 baselines, found %s" % len(baselines)
        )

        baseline1.delete()

        self.assertTrue(
            baseline1.is_deleted,
            msg="Expected baseline1 to be deleted, it was not"
        )

        self.assertTrue(
            baseline1.dimbaseline.is_deleted,
            msg="Expected baseline1.dimbaseline to be deleted, it was not"
        )

        baselines = EMODBaseline.list_baselines(
            DimUser.objects.get(pk=1),
            with_deleted=False
        )

        self.assertEqual(
            len(baselines),
            1,
            msg="Expected only 1 non-deleted scenario, found %s" % len(baselines)
        )

        baseline2.is_deleted = True

        self.assertTrue(
            baseline1.is_deleted,
            msg="Expected baseline2 to be deleted, it was not"
        )

        self.assertTrue(
            baseline1.dimbaseline.is_deleted,
            msg="Expected baseline2.dimbaseline to be deleted, it was not"
        )




    def test_list_baselines(self):
        """
        Here we test the list baselines method
        """
        baseline = EMODBaseline(
            name="Testing list",
            description="Testing list",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        baseline.save()

        bls = EMODBaseline.list_baselines(
            user=DimUser.objects.get(pk=1)
        )

        self.assertEqual(
            len(bls),
            1,
            msg="Expected 1 scenario, found %s" % len(bls)
        )

        self.assertEqual(
            bls[0]['name'],
            'Testing list',
            msg="Baseline not properly listed, expected 'Testing List' as name, received %s" % bls[0]['name']
        )

    def test_get_on_not_saved(self):
        """
        Here we test to make sure the get_files fails when the scenario object is not saved
        """
        baseline = EMODBaseline(
            name="Testing failed get",
            description="Testing failed get",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )

        self.assertRaises(
            ObjectDoesNotExist,
            baseline.get_files
        )

    def test_save_wrong_model(self):
        """
        Here we test to make sure we get appropriate errors when we attempt to use EMODBaseline for the wrong model
        """
        self.assertRaisesMessage(
            ValueError,
            "EMODBaseline can only be used with EMOD Models",
            EMODBaseline,
            name="Testing Failed Model",
            description="Testing Failed Model",
            model=DimModel.objects.get(pk=2),
            user=DimUser.objects.get(pk=1)
        )

        baseline = EMODBaseline(
            name="Testing Failed Model Save",
            description="Testing Failed Model Save",
            user=DimUser.objects.get(pk=1),
        )

        baseline.model = DimModel.objects.get(pk=2)

        self.assertRaises(
            ValueError,
            baseline.save
        )

    def test_save(self):
        """
        We generate temporary files and attach them to a scenario.  We then see if that scenario object has the correct
        files and also if the DimBinFiles objects sees them.
        """
        baseline = EMODBaseline()
        baseline._name = "Testing the scenario"
        baseline._description = "Testing the scenario object, complete EMOD scenario"
        qs = DimModel.objects.filter(model='EMOD')
        baseline.model = qs[0]
        baseline.user = DimUser.objects.get(pk=1)

        self.assertEqual(
            baseline.has_required_files,
            False,
            msg="Baseline completeness at creation is supposed to be False, found %s" % baseline.has_required_files
        )

        self.assertEqual(
            len(baseline.files),
            0,
            msg="Before files are added, we expect 0 files, found %s" % len(baseline.files)
        )

        self.assertRaises(
            ObjectDoesNotExist,
            baseline.get_files
        )

        fdict = dict()
        for rf in baseline.required_filetypes:
            f, path = tempfile.mkstemp()
            rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
            os.write(f, rand_str)
            os.close(f)
            m = hashlib.md5()
            m.update(rand_str)
            fhash = m.hexdigest()
            fdict[rf] = {'handle': f, 'path': path, 'hash': fhash}
            baseline.add_file(rf, path, name=rf, description='Testing %s type' % rf)

        bid = baseline.save()
        self.assertEqual(
            baseline.id,
            bid[0],
            msg="Expected scenario id of %s, found %s" % (bid[0], baseline.id)
        )

        self.assertEqual(
            len(baseline.files),
            len(baseline.required_filetypes),
            msg="Expected %s files, found %s files" % (len(baseline.files), len(baseline.required_filetypes))
        )

        qs = baseline.dimbaseline.binfiles.all()
        ids = map(lambda x: x['id'], baseline.files)
        for f in qs:
            self.assertIn(
                f.id,
                ids,
                msg="File %s was not in the scenario file list" % f.id
            )

        self.assertEqual(
            len(qs),
            len(baseline.get_files()),
            msg="Expected %s files, found %s attached to scenario via get_files" % (len(qs), len(baseline.get_files()))
        )

        self.assertEqual(
            bid[1],
            baseline.has_required_files,
            msg="Completeness from scenario save (%s) and has_required_files (%s) disagree" % (bid[1], baseline.has_required_files)
        )

        self.assertEqual(
            bid[1],
            baseline.dimbaseline.is_completed,
            msg="Completeness from scenario save (%s) and DimBaseline.is_completed (%s) disgree" % (
                bid[1],
                baseline.dimbaseline.is_completed
            )
        )

        for ftype in baseline.required_filetypes:
            dbf = baseline.get_file_by_type(ftype)
            self.assertEqual(
                dbf.file_hash,
                fdict[ftype]['hash'],
                msg="Hash for file type %s incorrect.  Expected %s, found %s" % (
                    ftype,
                    dbf.file_hash,
                    fdict[ftype]['hash']
                )
            )

            m = hashlib.md5()
            m.update(dbf.content)
            fhash = m.hexdigest()
            self.assertEqual(
                dbf.file_hash,
                fhash,
                msg="Hash of content (%s) and stored hash (%s) disagree.  File saved incorrectly" % (
                    dbf.file_hash,
                    fhash
                )
            )

        self.assertRaises(
            ObjectDoesNotExist,
            baseline.get_file_by_type,
            'Not a type'
        )

        airjson, airbin = baseline.get_air_file(binfile=True, jsonfile=True)
        self.assertEqual(
            airjson.file_name,
            'air json',
            msg="Air json file was saved incorrectly, expected file name 'air json', found %s" % airjson.file_name
        )
        self.assertEqual(
            airbin.file_name,
            'air binary',
            msg="Air json file was saved incorrectly, expected file name 'air binary', found %s" % airjson.file_name
        )
        
        humidityjson, humiditybin = baseline.get_humidity_file(binfile=True, jsonfile=True)
        self.assertEqual(
            humidityjson.file_name,
            'humidity json',
            msg="Air json file was saved incorrectly, expected file name 'humidity json', found %s" %
                humidityjson.file_name
        )
        self.assertEqual(
            humiditybin.file_name,
            'humidity binary',
            msg="Air json file was saved incorrectly, expected file name 'humidity binary', found %s" %
                humidityjson.file_name
        )
        
        land_tempjson, land_tempbin = baseline.get_land_temp_file(binfile=True, jsonfile=True)
        self.assertEqual(
            land_tempjson.file_name,
            'land_temp json',
            msg="Air json file was saved incorrectly, expected file name 'land_temp json', found %s" %
                land_tempjson.file_name
        )
        self.assertEqual(
            land_tempbin.file_name,
            'land_temp binary',
            msg="Air json file was saved incorrectly, expected file name 'land_temp binary', found %s" %
                land_tempjson.file_name
        )
        
        rainfalljson, rainfallbin = baseline.get_rainfall_file(binfile=True, jsonfile=True)
        self.assertEqual(
            rainfalljson.file_name,
            'rainfall json',
            msg="Air json file was saved incorrectly, expected file name 'rainfall json', found %s" %
                rainfalljson.file_name
        )
        self.assertEqual(
            rainfallbin.file_name,
            'rainfall binary',
            msg="Air json file was saved incorrectly, expected file name 'rainfall binary', found %s" %
                rainfalljson.file_name
        )

        campaign = baseline.get_campaign_file()
        self.assertEqual(
            campaign.file_name,
            'campaign',
            msg="Campaign File was saved incorrectly, expected file name 'campaign', found %s" % campaign.file_name
        )

        config = baseline.get_config_file()
        self.assertEqual(
            config.file_name,
            'config',
            msg="Config File was saved incorrectly, expected file name 'config', found %s" % config.file_name
        )

    def test_named_add(self):
        """
        This tests the named add file methods in the EMOD Baseline
        """
        baseline = EMODBaseline()
        baseline._name = "Testing the scenario"
        baseline._description = "Testing the scenario object, complete EMOD scenario"
        qs = DimModel.objects.filter(model='EMOD')
        baseline.model = qs[0]
        baseline.user = DimUser.objects.get(pk=1)

        f, path = tempfile.mkstemp()
        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
        m = hashlib.md5()
        m.update(rand_str)
        fhash = m.hexdigest()
        os.write(f, rand_str)
        os.close(f)

        baseline.add_air_file(path, name='air json', description='testing air json named method', jsonfile=True)
        baseline.add_air_file(path, name='air binary', description='testing air bin named method', jsonfile=False)

        baseline.save()
        self.assertFalse(
            baseline.has_required_files,
            msg="Baseline reports completed when it is not"
        )
        qs = DimBaseline.objects.all()

        self.assertEqual(
            len(qs),
            1,
            msg="Another scenario was created, expected 1 scenario, found %s" % len(qs)
        )

        airjson, airbin = baseline.get_air_file(binfile=True, jsonfile=True)
        self.assertEqual(
            airbin.file_name,
            'air binary',
            msg="Air Binary file saved incorrectly"
        )
        self.assertEqual(
            airjson.file_name,
            'air json',
            msg="Air JSON file saved incorrectly"
        )
        
        baseline.add_humidity_file(path, name='humidity json', description='humidity json named method', jsonfile=True)
        baseline.add_humidity_file(path, name='humidity binary', description='humidity binary named method', jsonfile=False)
        
        baseline.save()
        self.assertFalse(
            baseline.has_required_files,
            msg="Baseline reports completed when it is not"
        )
        qs = DimBaseline.objects.all()

        self.assertEqual(
            len(qs),
            1,
            msg="Another scenario was created, expected 1 scenario, found %s" % len(qs)
        )
        
        self.assertEqual(
            len(baseline.files),
            4,
            msg="Expected 4 files on current scenario, found %s" % len(baseline.files)
        )
        humidityjson, humiditybin = baseline.get_humidity_file(binfile=True, jsonfile=True)
        self.assertEqual(
            humiditybin.file_name,
            'humidity binary',
            msg="Humidity Binary file saved incorrectly"
        )
        self.assertEqual(
            humidityjson.file_name,
            'humidity json',
            msg="Humidity JSON file saved incorrectly"
        )
        
        baseline.add_rainfall_file(path, name='rainfall json', description='rainfall json named method', jsonfile=True)
        baseline.add_rainfall_file(path, name='rainfall binary', description='rainfall binary named method', jsonfile=False)
        
        baseline.save()
        self.assertFalse(
            baseline.has_required_files,
            msg="Baseline reports completed when it is not"
        )
        qs = DimBaseline.objects.all()

        self.assertEqual(
            len(qs),
            1,
            msg="Another scenario was created, expected 1 scenario, found %s" % len(qs)
        )
        
        self.assertEqual(
            len(baseline.files),
            6,
            msg="Expected 6 files on current scenario, found %s" % len(baseline.files)
        )
        rainfalljson, rainfallbin = baseline.get_rainfall_file(binfile=True, jsonfile=True)
        self.assertEqual(
            rainfallbin.file_name,
            'rainfall binary',
            msg="Rainfall Binary file saved incorrectly"
        )
        self.assertEqual(
            rainfalljson.file_name,
            'rainfall json',
            msg="Rainfall JSON file saved incorrectly"
        )
        
        baseline.add_land_temp_file(path, name='land_temp json', description='land_temp json named method', jsonfile=True)
        baseline.add_land_temp_file(path, name='land_temp binary', description='land_temp binary named method', jsonfile=False)
        
        baseline.save()
        self.assertFalse(
            baseline.has_required_files,
            msg="Baseline reports completed when it is not"
        )
        qs = DimBaseline.objects.all()

        self.assertEqual(
            len(qs),
            1,
            msg="Another scenario was created, expected 1 scenario, found %s" % len(qs)
        )
        
        self.assertEqual(
            len(baseline.files),
            8,
            msg="Expected 8 files on current scenario, found %s" % len(baseline.files)
        )
        land_tempjson, land_tempbin = baseline.get_land_temp_file(binfile=True, jsonfile=True)
        self.assertEqual(
            land_tempbin.file_name,
            'land_temp binary',
            msg="Land_temp Binary file saved incorrectly"
        )
        self.assertEqual(
            land_tempjson.file_name,
            'land_temp json',
            msg="Land_temp JSON file saved incorrectly"
        )
        
        baseline.add_config_file(path, name="config", description="Testing config named method")
        
        baseline.save()
        self.assertFalse(
            baseline.has_required_files,
            msg="Baseline reports completed when it is not"
        )
        qs = DimBaseline.objects.all()

        self.assertEqual(
            len(qs),
            1,
            msg="Another scenario was created, expected 1 scenario, found %s" % len(qs)
        )
        
        config = baseline.get_config_file()
        self.assertEqual(
            config.file_name,
            'config',
            msg="Config file Saved Incorrectly"
        )
        
        baseline.add_campaign_file(path, name="campaign", description="Testing campaign named method")
        
        baseline.save()
        self.assertFalse(
            baseline.has_required_files,
            msg="Baseline reports completed when it is not"
        )
        qs = DimBaseline.objects.all()

        self.assertEqual(
            len(qs),
            1,
            msg="Another scenario was created, expected 1 scenario, found %s" % len(qs)
        )
        
        campaign = baseline.get_campaign_file()
        self.assertEqual(
            campaign.file_name,
            'campaign',
            msg="Campaign file Saved Incorrectly"
        )
        
        baseline.add_demographics_file(path, name="demographics", description="Testing demographics named method")
        
        baseline.save()
        self.assertTrue(
            baseline.has_required_files,
            msg="Baseline reports incompleted when it is"
        )
        qs = DimBaseline.objects.all()

        self.assertEqual(
            len(qs),
            1,
            msg="Another scenario was created, expected 1 scenario, found %s" % len(qs)
        )
        
        demographics = baseline.get_demographics_file()
        self.assertEqual(
            demographics.file_name,
            'demographics',
            msg="Demographics file Saved Incorrectly"
        )

    def test_versioning(self):
        """
        This tests the versioning aspect of the Baseline.  First, we create a complete scenario, then change a file
        and see if a new Baseline of a different version is created.
        """
        baseline = EMODBaseline(
            name="Test Versioning",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )
        file_types = [
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

        self.assertEqual(file_types, baseline.required_filetypes)

        for ftype in file_types:
            if 'binary' in ftype:
                name = '%s binary' % ftype.split(' ')[0]
            elif 'json' in ftype:
                name = '%s json' % ftype.split(' ')[0]
            else:
                name = '%s' % ftype

            f, path = tempfile.mkstemp()

            rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

            os.write(f, rand_str)
            os.close(f)

            baseline.add_file(ftype, path, name=name, description='test test')
        baseline._name = "Test Baseline"
        baseline._description = "Test Baseline"
        baseline.user = DimUser.objects.get(pk=1)
        baseline.model = DimModel.objects.get(pk=1)
        baseline.save()

        qs = DimBaseline.objects.all()
        self.assertEqual(
            len(qs),
            1,
            msg="Expected only 1 scenario, found %s" % len(qs)
        )

        self.assertTrue(
            baseline.has_required_files,
            msg="Baseline reporting incomplete when it is"
        )

        self.assertTrue(
            baseline.dimbaseline.is_completed,
            msg="DimBaseline reporting incomplete when it is"
        )

        f, path = tempfile.mkstemp()
        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
        os.write(f, rand_str)
        os.close(f)
        m = hashlib.md5()
        m.update(rand_str)
        fhash = m.hexdigest()

        orig_id = baseline.id
        orig_version = baseline.dimbaseline.version

        added = baseline.add_config_file(path, name="New Config File", description="Testing Versioning")

        self.assertTrue(
            added,
            msg="Failed to add Baseline File"
        )

        baseline.save()

        self.assertEqual(
            orig_id,
            baseline.id,
            msg="Created new scenario before approval"
        )

        self.assertNotEqual(
            baseline.dimbaseline.version,
            orig_version,
            msg="New timestamp not saved"
        )

        baseline.is_approved = True

        self.assertTrue(
            baseline.is_approved,
            msg="Baseline failed to set approved status"
        )

        self.assertTrue(
            baseline.dimbaseline.is_approved,
            msg="DimBaseline failed to set approved status"
        )

        f, path = tempfile.mkstemp()
        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
        os.write(f, rand_str)
        os.close(f)
        m = hashlib.md5()
        m.update(rand_str)
        fhash = m.hexdigest()

        added = baseline.add_config_file(path, name="New new Config File", description="Testing Versioning")

        self.assertTrue(
            added,
            msg="Failed to add Baseline File"
        )

        baseline.save()

        self.assertNotEqual(
            orig_id,
            baseline.id,
            msg="No new version was created: \n\tOriginal ID: %s \n\tNew ID: %s" % (orig_id, baseline.id)
        )

        self.assertNotEqual(
            baseline.dimbaseline.version,
            orig_version,
            msg="No new version was created: \n\tOriginal Version: %s \n\tNew Version: %s" % (
                baseline.version,
                orig_version
            )
        )

        self.assertTrue(
            orig_version < baseline.dimbaseline.version,
            msg="New version timestamp (%s) is older than original timestamp (%s)" % (
                baseline.dimbaseline.version,
                orig_version
            )
        )

        config = baseline.get_config_file()
        self.assertEqual(
            config.file_name,
            'New new Config File',
            msg="New new Config file was not saved."
        )

        qs = DimBaseline.objects.all()
        self.assertEqual(
            len(qs),
            2,
            msg="Expected 2 DimBaseline Objects, found %s" % len(qs)
        )

        bls = EMODBaseline.list_baselines(
            DimUser.objects.get(pk=1)
        )

        # import pdb; pdb.set_trace()

        self.assertEqual(
            len(bls),
            1,
            msg="Expected a single scenario to be returned, received %s" % len(bls)
        )

        # import pdb;pdb.set_trace()
        self.assertEqual(
            bls[0]['version'],
            baseline.version,
            msg="Versions mismatch"
        )

    def test_missing_files(self):
        """
        Here we test to make sure that missing files are reported correctly.
        """

        baseline = EMODBaseline(
            name="Testing missing_files",
            model=DimModel.objects.get(pk=1),
            user=DimUser.objects.get(pk=1)
        )
        baseline.user = DimUser.objects.get(pk=1)
        baseline.model = DimModel.objects.get(pk=1)
        f, path = tempfile.mkstemp()
        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
        os.write(f, rand_str)
        os.close(f)

        baseline.add_air_file(path, name='air json', jsonfile=True)
        baseline.add_air_file(path, name='air binary', jsonfile=False)
        baseline._name = "Testing missing files"
        baseline._description = "Testing missing files"
        baseline.save()

        missing_files = baseline.get_missing_files()
        in_missing = any([x in missing_files for x in ['air json', 'air binary']])
        self.assertFalse(
            in_missing,
            msg="Air JSON/binary files are in the missing files list"
        )

        self.assertEqual(
            len(missing_files),
            9,
            msg="Expected 9 missing files, found %s" % len(missing_files)
        )

        baseline.add_config_file(path, name='config')
        baseline.save()

        missing_files = baseline.get_missing_files()
        self.assertFalse(
            'config' in missing_files,
            msg="Config file (added) is in missing files list"
        )

        self.assertEqual(
            len(missing_files),
            8,
            msg="Expected 8 missing files, found %s" % len(missing_files)
        )

    def test_approval(self):
        """
        This will test the approval logic, making sure errors are thrown when necessary and only setting approval
        status when the scenario is complete.
        """

        baseline = EMODBaseline(
            name="Testing Approval",
            description="Testing Approval Logic",
            user=DimUser.objects.get(pk=1),
            model=DimModel.objects.get(pk=1)
        )

        try:
            baseline.is_approved = True
            self.assertFalse(True, msg="Failed to raise approval exception on unsaved scenario")
        except ValueError as err:
            self.assertEqual(
                "Approval can only be set once a scenario has been saved",
                str(err),
                msg="Incorrect exception raised.  Expected save error, received: %s" % err
            )

        baseline.save()

        try:
            baseline.is_approved = 5
            self.assertFalse(True, msg="Failed to raise TypeError")
        except TypeError as err:
            self.assertEqual(
                "Parameter status must be a boolean, received %s" % type(5),
                str(err),
                msg="Incorrect exception raised.  Expected type error message, received : %s" % err
            )

        try:
            baseline.is_approved = True
            self.assertFalse(True, msg="Failed to raise has_required_files exception")
        except ValueError as err:
            self.assertEqual(
                "Baseline is not complete, and cannot be approved",
                str(err),
                msg="Incorrect exception raised. Expected has_required_files error, received: %s" % err
            )

        file_types = [
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

        self.assertEqual(file_types, baseline.required_filetypes)

        for ftype in file_types:
            if 'binary' in ftype:
                name = '%s binary' % ftype.split(' ')[0]
            elif 'json' in ftype:
                name = '%s json' % ftype.split(' ')[0]
            else:
                name = '%s' % ftype

            f, path = tempfile.mkstemp()

            rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))

            os.write(f, rand_str)
            os.close(f)

            baseline.add_file(ftype, path, name=name, description='test test')

        baseline.save()

        self.assertTrue(
            baseline.has_required_files,
            msg="Baseline is reporting icomplete when it is"
        )

        try:
            baseline.is_approved = True
        except Exception as err:
            self.assertFalse(True, msg="Raise exception %s" % err)

        self.assertTrue(
            baseline.is_approved,
            msg="Failed to set approval status to True"
        )

    def test_edit_file(self):
        """
        Here we test that editing a file, changing a files contents and hash, will overwrite the file if the scenario is
        not complete or not approved.  If it is complete and approved, editting a file in this manner will create a new
        scenario.
        """
        baseline1 = EMODBaseline(
            name="First test scenario for file editing",
            description="First of two baselines",
            user=DimUser.objects.get(pk=1),
            model=DimModel.objects.get(pk=1)
        )

        baseline2 = EMODBaseline(
            name="Second test scenario for file editing",
            description="Second of two baselines",
            user=DimUser.objects.get(pk=1),
            model=DimModel.objects.get(pk=1)
        )

        f, path = tempfile.mkstemp()
        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
        os.write(f, rand_str)
        os.close(f)

        baseline1.add_file('config', path, name='Test Config', description='Test Config File')
        baseline1.save()
        baseline2.add_file('config', path, name='Test Config', description='Test Config File')
        baseline2.save()

        conf1 = baseline1.get_config_file()
        conf2 = baseline2.get_config_file()

        self.assertEqual(
            conf1.id,
            conf2.id,
            msg="Failed to add same file to multiple baselines"
        )

        f, path = tempfile.mkstemp()
        rand_str = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(1000))
        os.write(f, rand_str)
        os.close(f)

        orig1_id = baseline1.id
        baseline1.add_file('campaign', path, name='Test Campaign')
        baseline1.save()

        self.assertEqual(
            orig1_id,
            baseline1.id,
            msg="Created new version before complete and approved"
        )

        camp1_1 = baseline1.get_campaign_file()
        camp1_1_id = camp1_1.id
        camp1_1_hash = camp1_1.file_hash
        camp1_len = len(baseline1.files)

        with open(path, 'w') as f:
            rand_str += "MORE CHARACTERS"
            f.write(rand_str)

        baseline1.add_file('campaign', path, name='Test Campaign')
        baseline1.save()

        camp1_2 = baseline1.get_campaign_file()

        # import pdb; pdb.set_trace()
        self.assertEqual(
            camp1_len,
            len(baseline1.files),
            msg="Did not remove old file for new one"
        )

        self.assertNotEqual(
            camp1_1_hash,
            camp1_2.file_hash,
            msg="Hash did not change, edit not applied"
        )

        baseline2.add_file('campaign', path, name='Test Campaign')
        m = hashlib.md5()
        m.update(rand_str)
        o2hash = m.hexdigest()

        #import pdb; pdb.set_trace()
        baseline2.save()
        camp2 = baseline2.get_campaign_file()

        self.assertEqual(
            camp2.file_hash,
            o2hash,
            msg="Failed to save appropriate file to baseline2"
        )

        with open(path, 'w') as f:
            rand_str += "EVEN MORE CHARACTERS"
            f.write(rand_str)

        m = hashlib.md5()
        m.update(rand_str)
        o1hash = m.hexdigest()

        self.assertNotEqual(
            o1hash,
            o2hash,
            msg="Failed to re-create file"
        )

        added = baseline1.add_file('campaign', path, name='Test Campaign')
        self.assertTrue(
            added,
            msg="Failed to add file to scenario"
        )
        baseline1.save()

        camp1 = baseline1.get_campaign_file()
        self.assertEqual(
            camp1.file_hash,
            o1hash,
            msg="Failed to save appropriate file to baseline1"
        )

        self.assertNotEqual(
            camp1.id,
            camp2.id,
            msg="Edited file attached to multiple baselines"
        )

        os.remove(path)
