########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################

__author__ = 'lselvy'

from django.test.simple import DjangoTestSuiteRunner, get_tests, build_test, reorder_suite, get_app, get_apps
#from django.test import TestCase
from django.test import _doctest as doctest
from django.test.testcases import OutputChecker, DocTestRunner
from selenium import webdriver
import unittest
import inspect
from optparse import make_option

from . import test_settings

TEST_MODULE = 'tests'                           #:
doctestOutputChecker = OutputChecker()
accepted_browsers = ['firefox', 'ie','chrome']  #:



def get_browser(browser_name):
    """This is a function that gets the browser class from a string name.

    This is just a decision tree for transforming strings into browser classes.

    :param str browser_name: A string containing the name of the browser [firefox,chrome,ie]
    """
    if browser_name == 'chrome': browser = webdriver.Chrome
    elif browser_name == 'ie': browser = webdriver.Ie
    else: browser = webdriver.Firefox

    return browser

def build_suite(app_module, test_type, host):
    """
    Create a complete Django test suite for the provided application module.
    """
    suite = unittest.TestSuite()

    # Load unit and doctests in the models.py module. If module has
    # a suite() method, use it. Otherwise build the test suite ourselves.
    if hasattr(app_module, 'suite'):
        suite.addTest(app_module.suite())
    else:
        suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(
            app_module))
        try:
            suite.addTest(doctest.DocTestSuite(app_module,
                                               checker=doctestOutputChecker,
                                               runner=DocTestRunner))
        except ValueError:
            # No doc tests in models.py
            pass

    # Check to see if a separate 'tests' module exists parallel to the
    # models module
    test_module = get_tests(app_module)
    if test_module:
        # Load unit and doctests in the tests.py module. If module has
        # a suite() method, use it. Otherwise build the test suite ourselves.
        if hasattr(test_module, 'suite'):
            suite.addTest(test_module.suite())
        else:
            # Add the tests to the test suite based on test_type selected and
            # the attribute "type" of the class
            for name,obj in inspect.getmembers(test_module):
                if not inspect.isclass(obj): continue
                setattr(obj, 'host', host)
                if test_type == 'both':
                    suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(obj))
                    continue
                if hasattr(obj, 'test_type'):
                    if test_type == 'funct' and getattr(obj, 'test_type') == 'funct':
                        suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(obj))
                        continue
                    elif getattr(obj, 'test_type') == 'unit' and test_type == 'unit':
                        suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(obj))
                        continue
                else:
                    if test_type == 'unit':
                        suite.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(obj))
                        continue
            # suite.addTest(unittest.defaultTestLoader.loadTestsFromModule(
            #     test_module))
            try:
                suite.addTest(doctest.DocTestSuite(
                    test_module, checker=doctestOutputChecker,
                    runner=DocTestRunner))
            except ValueError:
                # No doc tests in tests.py
                pass
    return suite

class Test_Runner(DjangoTestSuiteRunner):
    """This class is a test runner for the the VecNet CI

    This is an extension of the default django test runner which will differentiate between
    Functional Tests and Unit Tests, allowing you to run either or both.  It also allows for
    further definition of a browser to use for functional tests (by default Firefox).
    """
    option_list = (make_option("-b", "--browser", action="store", type="string", dest="browser",
                               help="Browser that the functional tests should be run in"),
                   make_option("--type", action="store", type="string", dest="type",
                               help="Functional Tests/Units Tests or both [funct,unit,both]"),
                   make_option("--host", action="store", type="string", dest="host",
                               help="Host to be used in functional tests, ie the base url.  Ex: http://locahost:8000"))
    test_type = "both"
    host = "http://localhost:8000"
    browser = "firefox"

    def __init__(self, verbosity=1, interactive=True, failfast=True, **kwargs):
        self.verbosity = test_settings.verbosity = verbosity
        self.failfast = test_settings.failfast = failfast
        self.interactive = test_settings.interactive = interactive
        if kwargs['browser'] is not None: self.browser = kwargs['browser'].lower()
        if kwargs['type'] is not None: self.test_type = kwargs['type'].lower()
        if kwargs['host'] is not None: self.host = kwargs['host']

    def build_suite(self, test_labels, extra_tests=None, **kwargs):
            suite = unittest.TestSuite()

            if test_labels:
                for label in test_labels:
                    if '.' in label:
                        suite.addTest(build_test(label))
                    else:
                        app = get_app(label)
                        suite.addTest(build_suite(app, self.test_type, self.host))
            else:
                for app in get_apps():
                    suite.addTest(build_suite(app, self.test_type, self.host))

            if extra_tests:
                for test in extra_tests:
                    suite.addTest(test)

            return reorder_suite(suite, (unittest.TestCase,))

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        self.setup_test_environment()
        suite = self.build_suite(test_labels, extra_tests)
        old_config = self.setup_databases()
        # We run the suite once for each browser
        for browse in self.browser.split(','):
            # Now we reassign all the browser variables to the new browser

            for test in suite:
                setattr(test, 'browser', browse)
            result = self.run_suite(suite)
        self.teardown_databases(old_config)
        self.teardown_test_environment()
        return self.suite_result(suite, result)
