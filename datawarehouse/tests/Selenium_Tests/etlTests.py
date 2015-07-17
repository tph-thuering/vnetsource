########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################

# import statements
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
import unittest, time, re


class CheckAllBoxes(unittest.TestCase):
    # TODO Add class docstring
    # TODO Add method docstring(s)
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)
        self.base_url = "http://localhost:8005/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def test(self):
        driver = self.driver
        driver.get(self.base_url + "datawarehouse/LookUpTable")
        self.checkAll()
        self.checkAllBoxes()
        self.checkAllBoxes()
        self.checkAll()

    def checkAllBoxes(self):
        driver = self.driver
        counter = 0
        boxes = len(driver.find_elements_by_css_selector('.active .toggleBox'))
        while counter < boxes:
            driver.find_elements_by_css_selector('.active .toggleBox')[counter].click()
            counter = counter+1

    def checkAll(self):
        driver = self.driver
        driver.find_element_by_css_selector('.active .checkAll').click()

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True
    
    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True
    
    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True
    
    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
