########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Robert Jones <Robert.Jones.428@nd.edu>
########################################################################################################################

import unittest
from selenium import webdriver

class ScenarioTest(unittest.TestCase):
    # TODO Add class docstring
    # TODO Add method docstring(s)

    def setUp(self):
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(3)

    def tearDown(self):
        self.browser.quit()

    def test_vecnet_found(self):
        # Start out on the homepage of the VecNet tools:
        self.browser.get('http://localhost:8000')

        # Check that we got a VecNet page
        self.assertIn('Welcome to VecNet', self.browser.title) #"Browser title was:\n" + self.browser.title
        #self.fail('Fails here all the time!')

# Choosing EMOD Expert Interface in the Tools menu 

# should bring us to "Welcome to EMOD Expert Interface"







if __name__ == '__main__':
    unittest.main()
