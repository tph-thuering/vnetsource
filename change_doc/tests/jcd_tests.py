"""
This package contains the unittests and functional tests for the JSON Change Document (JCD) class
"""

import json
from unittest import TestCase
from copy import deepcopy
from change_doc.jcd import JCD


class jcdTests(TestCase):
    """
    This will test the functionality of all the JCD methods
    """

    jcd_file = "data_services/tests/static_files/changeDoc.json"    #: Changes document file

    def setUp(self):
        """
        Here we setup all the objects we will need in the tests.  Namely, we read in the jcd_file
        and get that into an object.
        """
        ofile = file(self.jcd_file, "r")
        self.jcd = json.loads(ofile.read())         #: Good JCD for the tests
        ofile.close()

        self.bad_jcd = deepcopy(self.jcd)           #: Bad JCD for the tests
        self.bad_jcd.pop("Changes", None)

    def testinit(self):
        """
        This will test the init method to make sure it sets the JCD of the class properly
        """

        #------ Test the failure of a bad JCD
        self.assertRaises(
            ValueError,
            JCD,
            self.bad_jcd
        )

        #------- Instantiate a good JCD

        jcd = JCD(self.jcd)

        self.assertEqual(
            jcd.jcd,
            self.jcd,
            msg="Improper JCD assignment"
        )
        #-------- Test loading from bad string

        s_bad_jcd = json.dumps(self.bad_jcd)

        self.assertRaises(
            ValueError,
            JCD,
            s_bad_jcd
        )

        #-------- Test loading from string
        s_jcd = json.dumps(self.jcd)

        jcd2 = JCD(s_jcd)

        self.assertEqual(
            jcd2.jcd,
            self.jcd,
            msg="Improper JCD assignment from string"
        )

    def testgetarms(self):
        """
        Here we will test the _get_arms method (classmethod) of the JCD to make sure it can give us the appropriate
        arm information.  As the object method is just a wrapper for this, it will not be tested separately.
        """
        arms = JCD._get_factorables(self.jcd)

        self.assertEqual(
            arms[0],
            (4, ["mosquito1 + mosquito2", "-mosquito1", "+mosquito2"]),
            msg="Multi mosquito sweep not detected properly"
        )

        self.assertEqual(
            arms[1],
            (5, ["sweep1"]),
            msg="Sweep not detected properly"
        )

        #------ Test getarms on a bad JCD
        self.assertRaises(
            ValueError,
            JCD._get_factorables,
            self.bad_jcd
        )