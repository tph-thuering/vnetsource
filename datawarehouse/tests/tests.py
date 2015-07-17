########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu
########################################################################################################################

import unittest
import cubes
from datawarehouse.cubes_config import engine, dwmodel
from datawarehouse.models import fact_prefix, dimension_prefix


class CubesTestCase(unittest.TestCase):

    def test_model(self):
        """
        Making sure the model can be loaded and is valid
        """
        filename = 'datawarehouse/fixtures/datawarehouse.json'
        model = cubes.load_model(filename)
        self.assertIsInstance(model,cubes.model.Model)

    def test_cubes(self):
        """
        Testing that each cube can be instantiated
        Testing that facts in each cube can be called

        This will insure that you can aggregate and get
        raw data from each of the cubes in the model used
        by the datawarehouse.  This should work when you
        change schema and add when you add cubes.
        """
        filename = 'datawarehouse/fixtures/datawarehouse.json'
        workspace = cubes.create_workspace('sql',dwmodel,engine=engine,fact_prefix=fact_prefix,dimension_prefix=dimension_prefix)
        for c_key,c_name in dwmodel.cubes.iteritems():
            cube = dwmodel.cube(c_name)
            self.assertIsInstance(cube,cubes.model.Cube)
            try:
                # If mapping is explicitly defined, grab the explicit mapping for key
                cube.key = cube.mappings['id']
            except (TypeError,KeyError):
                # Otherwise either no mappings are listed or a mapping for 'id' does not exist
                pass
            try:
                browser = workspace.browser(cube)
            except Exception as error:
                print "Cube: " + c_key + " Failed"
                print error
                assert False
            self.assertIsInstance(browser,cubes.backends.sql.star.SnowflakeBrowser)
            cell = cubes.Cell(cube)
            try:
                facts = browser.facts(cell)
            except Exception as error:
                print "Cube: " + c_key + " Failed"
                print error
                assert False
            assert True
            print "Cube: " + c_key + " Passed"

