########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
#   Lawrence Selvy <Lawrence.Selvy.1@nd.edu>
#   Zachary Torstrick <Zachary.R.Torstrick.1@nd.edu>
########################################################################################################################
__author__ = 'lselvy'

from unittest import TestCase
from selenium import webdriver
from VECNet.testrunner import get_browser
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import WebDriverException

"""
These are the selenium functional tests for the Data warehouse browser
"""



class FunctionalTests_UI(TestCase):
    """This is a class defining the UI functional tests for the Data warehouse browser

    This tests adding in dimensions and measures to both the Dataset selector and the data slicer.
    This also tests that slices are created appropriately and the reset page button.
    """
    # TODO: test the remove all links

    test_type= "funct"
    host = "http://localhost:8000"
    browser = "firefox"

    def setUp(self):
        """This is a method that sets up the functional selenium test
        """
        print self.host
        init = get_browser(self.browser)
        self.browser = init()
        self.browser.get(self.host + '/datawarehouse/cube')
        self.browser.implicitly_wait(20)
        self.assertIn('Datawarehouse: Overview', self.browser.title,
                      msg="Title not found, page most likely did not load")
        cube_select = self.browser.find_element_by_id('cube')
        cubes = cube_select.find_elements_by_tag_name('option')
        cubes[3].click()
        self.browser.implicitly_wait(30)

    def tearDown(self):
        """This is a method that closes the Firefox browser instance when the test is finished.
        """
        self.browser.quit()

    def test_UI(self):
        """This is a method that tests the UI of the data warehouse browser

        This is left as one long test due to the time it takes to open and close
        the Firefox browser.  This tests the drag and drop functionality for the both
        dimensions and measures for both the Dataset Selector and the Data Slicer.
        It also tests that slices are made correctly and that the reset page button
        works as expected (clears the page).
        """
        # Grab the dimensions associated with this particular cube
        dimensions = self.browser.find_elements_by_css_selector('#dimensions .dim')
        self.assertEqual(
            len(dimensions),
            4,
            msg="Incorrect number of dimensions, expected 4, got {0}".format(len(dimensions))
        )

        # Grab the measures associated with this particular cube
        measures = self.browser.find_elements_by_css_selector('#measures .meas')
        self.assertEqual(
            len(measures),
            10,
            msg="Incorrect number of measures, expected 10, got {0}".format(len(measures))
        )

        target_div = self.browser.find_element_by_id('infobar')

        # Test Drag and Drop functionality for all dimensions.
        for dim in dimensions:
            ActionChains(self.browser).drag_and_drop(dim, target_div).perform()
            dim_in_infobar = self.browser.find_element_by_css_selector(
                '#infobar [data-name="{0}"]'.format(dim.get_attribute('id'))
            )
            self.assertIsNot(
                dim_in_infobar,
                None,
                msg="Drag and drop of dimension {0} to infobar failed".format(dim.get_attribute('id'))
            )

        # Test Drag and Drop functionality for all measures
        for meas in measures:
            ActionChains(self.browser).drag_and_drop(meas, target_div).perform()
            meas_in_infobar = self.browser.find_element_by_css_selector(
                '#infobar [data-name="{0}"]'.format(meas.get_attribute('id'))
            )
            self.assertIsNot(
                meas_in_infobar,
                None,
                msg="Drag and drop of measure {0} to infobar failed".format(meas.get_attribute('id'))
            )

        # Select Data Slicer tab and test drag and drop of dimension and measure
        self.browser.find_element_by_css_selector('[href="#RCT"]').click()
        #self.browser.implicitly_wait(100)
        self.assertEqual(
            self.browser.find_element_by_css_selector('#infobar .active').get_attribute('id'),
            "RCT",
            msg="Selection of the Data Slicer tab failed"
        )

        # Test the drag and drop of dimension to data slicer
        for dim in dimensions:
            ActionChains(self.browser).drag_and_drop(dim, target_div).perform()
            self.assertEqual(
                self.browser.find_element_by_id('RCTName').text,
                dim.get_attribute('data-type'),
                msg="Drag and drop for dimension {0} to Data Slicer failed".format(dim.get_attribute('id'))
            )

        # Test the drag and drop of measure to data slicer
        for meas in measures:
            # Set the implicity wait time to 1 second (should be long enough to see if they would
            # load when they shouldn't
            self.browser.implicitly_wait(1)
            no_slices = self.browser.find_elements_by_css_selector(
                '[data-caller="{0}"]'.format(meas.get_attribute('id')))
            ActionChains(self.browser).drag_and_drop(meas, target_div).perform()
            self.assertNotIn(
                self.browser.find_element_by_id('RCTName').text,
                meas.get_attribute('data-type'),
                msg="Drag and drop for measure {0} to Data Slicer succeeded, expected failure".format(
                    meas.get_attribute('id')
                )
            )
            #self.browser.find_elements_by_css_selector('#RCT [id="{0}"]'.format(meas.get_attribute('id')))
        self.browser.implicitly_wait(30)            # Reset the implicit wait time to 30 seconds

        # Test Slicing (make a slice using a specific example)
        test_slice = self.browser.find_element_by_css_selector('#dimensions #location')
        ActionChains(self.browser).drag_and_drop(test_slice, target_div).perform()
        region_select = self.browser.find_element_by_css_selector('#RCT #region')
        region_select.find_elements_by_tag_name('option')[3].click()
        country_select = self.browser.find_element_by_css_selector('#RCT #country')
        country_select.find_elements_by_tag_name('option')[3].click()
        text_check = '{0} > {1}|{2}'.format(
            test_slice.get_attribute('id'),
            region_select.get_attribute('value'),
            country_select.get_attribute('value')
        )
        self.browser.find_element_by_css_selector('#RCT .btn[data-caller="country"]').click()
        data_slice = self.browser.find_element_by_css_selector('#Slice_list .slice')
        self.assertEqual(
            data_slice.text,
            text_check,
            msg="Expected {0} for slice got {1}".format(data_slice.text, text_check)
        )

        # Test reset button
        self.browser.find_element_by_id('reset_page').click()
        slices = self.browser.find_elements_by_class_name('slice')
        datasets = self.browser.find_elements_by_class_name('dataset')
        self.assertEqual(
            len(slices),
            0,
            msg="Expected no slices, found {0}".format(len(slices))
        )
        self.assertEqual(
            len(datasets),
            0,
            msg="Expected no datasets (dimensions or measures), found {0}".format(len(datasets))
        )

class FunctionalTests_multiple_graphs_and_tables(TestCase):
    """This is a class defining tests for creating graphs and tables
    """
    test_type= "funct"
    host = "http://localhost:8000"
    browser = "firefox"

    def setUp(self):
        """This is the setup test method

        Here we setup the browser for the test class and retrieve the datawarehouse cube url
        We wait 10 seconds to make sure that the page loads
        """
        init = get_browser(self.browser)
        self.browser = init()
        self.browser = webdriver.Firefox()
        self.browser.implicitly_wait(30)                                            # Setup the implicit wait time
        self.browser.get(self.host + '/datawarehouse/cube')
        self.assertIn('Datawarehouse: Overview', self.browser.title,
                      msg="Title not found, page most likely did not load")
        cube_select = self.browser.find_element_by_id('cube')
        cubes = cube_select.find_elements_by_tag_name('option')
        cubes[3].click()

        # Use the select all for dimensions and measure to setup the test
        links = self.browser.find_elements_by_css_selector('#dataset_holder p a')
        for link in links: link.click()

    def tearDown(self):
        """Here we just close the browser that we used in this test
        """
        self.browser.quit()

    def test_multi_graph_and_tables(self):
        """This is a method for testing that graphs and tables are made correctly for the following cases

        Multiple dimensions and measures
        Multiple dimensions and measures with a single slice
        Multiple dimensions and measures with a multiple slices
        """
        dims = self.browser.find_elements_by_class_name('dim')
        dimension_names = []
        self.browser.find_element_by_id('create_graph').click()

        for dim in dims: dimension_names.append(dim.get_attribute('id'))

        charts = self.browser.find_elements_by_css_selector('.chart')
        chart_names = []
        for chart in charts: chart_names.append(chart.get_attribute('id'))
        graph_dims = self.browser.find_elements_by_css_selector('#xdiv .dataset')

        self.assertEqual(
            len(charts),
            len(graph_dims),
            msg="Expected {0} charts, received {1}".format(len(graph_dims), len(charts))
        )

        for dim in dimension_names:
            self.assertIn(
                dim,
                chart_names,
                msg='Dimensions {0} did not produce a graph'.format(dim)
            )

        # Now we use these selections to create tables
        self.browser.find_element_by_id('create_table').click()
        tables = self.browser.find_elements_by_class_name('dataTables_wrapper')
        self.assertEqual(
            len(dimension_names),
            len(tables),
            msg="Expected {0} tables, got {1}".format(len(dimension_names),len(tables))
        )

        for dim in dimension_names:
            self.assertIn(
                dim,
                chart_names,
                msg='Dimensions {0} did not produce a table'.format(dim)
            )

        # Now we make a slice and make sure that the graphs and tables are still generated
        self.browser.find_element_by_css_selector('[href="#RCT"]').click()
        self.browser.find_element_by_css_selector('#dimensions #location a').click()
        self.browser.find_elements_by_css_selector('#RCTCut #region option')[3].click()
        self.browser.find_element_by_css_selector('#RCTCut .btn[href="region"]').click()
        self.browser.find_element_by_id('create_graph').click()
        # This added the slice and created the graphs
        tables = self.browser.find_elements_by_class_name('dataTables_wrapper')
        self.assertEqual(
            len(dimension_names),
            len(tables),
            msg="Expected {0} tables, got {1}".format(len(dimension_names),len(tables))
        )

        # Now we try a second slice (this one on date)
        self.browser.find_element_by_css_selector('#dimensions #date a').click()
        start_years = self.browser.find_elements_by_css_selector('#from #year option')
        end_years = self.browser.find_elements_by_css_selector('#end #year option')
        for year in start_years:
            if year.get_attribute('value') == '2007': year.click()
        for year in end_years:
            if year.get_attribute('value') == '2008': year.click()
        self.browser.find_element_by_css_selector('#RCTCut .btn[data-caller="date"]').click()
        self.browser.find_element_by_id('create_graph').click()
        # This added the slice and created the graphs
        tables = self.browser.find_elements_by_class_name('dataTables_wrapper')
        self.assertEqual(
            len(dimension_names),
            len(tables),
            msg="Expected {0} tables, got {1}".format(len(dimension_names),len(tables))
        )

class FunctionalTest_single_graph_toolbar(TestCase):
    # TODO Add class docstring
    # TODO Add method docstring(s)
    test_type= "funct"
    host = "http://localhost:8000"
    browser = "firefox"

    def setUp(self):
        inst = get_browser(self.browser)
        self.browser = inst()
        self.browser.implicitly_wait(30)
        self.browser.get(self.host + '/datawarehouse/cube')
        self.browser.find_elements_by_css_selector('#cube option')[3].click()
        self.browser.find_element_by_css_selector('#dimensions #location a').click()
        self.browser.find_elements_by_css_selector('#dataset_holder p a')[1].click()
        self.browser.find_element_by_id('create_graph').click()

    def tearDown(self):
        self.browser.quit()

    def test_toolbar(self):
        self.browser.find_elements_by_css_selector('#window_graph_chooser option')[1].click()
        series = self.browser.find_elements_by_css_selector('#series-colors option')
        # First we test to see if the series colorpicker is filled when the graph_chooser is chosen

        self.assertEqual(
            len(series),
            10,
            msg="Expected 2 series (default and location), found {0}".format(len(series))
        )
        original_type = self.browser.execute_script(
            "return charts['default']['location'].options.chart.type;"
        )
        self.browser.find_element_by_id('chart_type').click()
        self.browser.find_elements_by_css_selector('.active .full_width ul li a')[1].click()
        new_type = self.browser.execute_script('return charts["default"]["location"].options.chart.type;')
        self.assertNotEqual(
            original_type,
            new_type,
            msg="Chart Type button failed to change chart type"
        )

        orig_state = self.browser.execute_script('return charts["default"]["location"].options.chart.inverted;')
        self.browser.find_element_by_id('invert').click()
        new_state = self.browser.execute_script('return charts["default"]["location"].options.chart.inverted;')
        self.assertNotEqual(
            orig_state,
            new_state,
            msg="Invert button failed to invert chart axes"
        )

        # We do not test colors as the color pickers don't lend themselves to testing.  That will have to be a visual
        # and manual test.  Now we move onto testing the Titles portion of the toolbar
        self.browser.find_element_by_css_selector('[href="#title_opts"]').click()
        self.browser.find_elements_by_css_selector('#text_graph_chooser option')[1].click()
        self.browser.find_element_by_id('graph_title').send_keys('Test Title')
        self.browser.find_element_by_id('graph_subtitle').send_keys('Test SubTitle')
        self.browser.find_element_by_id('graph_xtitle').send_keys('X Axis Test Title')
        self.browser.find_element_by_id('graph_ytitle').send_keys('Y Axis Test Title')
        self.browser.find_element_by_css_selector('.btn[value="Change Text"]').click()
        Title = self.browser.execute_script(
            'return charts.default.location.title.text;'
        )
        SubTitle = self.browser.execute_script(
            'return charts.default.location.subtitle.text;'
        )
        xAxisTitle = self.browser.execute_script(
            'return charts.default.location.xAxis[0].title.text;'
        )
        yAxisTitle = self.browser.execute_script(
            'return charts.default.location.yAxis[0].title.text;'
        )
        self.assertEqual(Title, 'Test Title', msg="Setting the title failed")
        self.assertEqual(SubTitle, 'Test SubTitle', msg='Setting the subtitle failed')
        self.assertEqual(xAxisTitle, 'X Axis Test Title', msg='Setting the X Axis Title failed')
        self.assertEqual(yAxisTitle, 'Y Axis Test Title', msg='Setting the Y Axis Title failed')

        # Now we move on to test the legend options
        self.browser.find_element_by_css_selector('[href="#legend_opts"]').click()
        self.browser.find_element_by_css_selector('#legend_graph_chooser option')[1].click()
        self.browser.find_element_by_id('legend_center').click()
        # First we test the center align
        new_state = self.browser.execute_script('return charts.default.location.legend.options.align;')
        self.assertEqual(
            new_state,
            'center',
            msg='Legend center align failed to set legend align value'
        )
        self.browser.find_element_by_id('legend_right').click()
        new_state = self.browser.execute_script('return charts.default.location.legend.options.align;')
        self.assertEqual(
            new_state,
            'right',
            msg='Legend right align failed to set legend align value'
        )
        self.browser.find_element_by_id('legend_left').click()
        new_state = self.browser.execute_script('return charts.default.location.legend.options.align;')
        self.assertEqual(
            new_state,
            'left',
            msg='Legend left align failed to set legend align value'
        )
        # Now we test the vertical align
        self.browser.find_element_by_id('legend_top').click()
        new_state = self.browser.execute_script('return charts.default.location.legend.options.verticalAlign;')
        self.assertEqual(
            new_state,
            'top',
            msg='Legend top align failed to set legend vertical align value'
        )
        self.browser.find_element_by_id('legend_middle').click()
        new_state = self.browser.execute_script('return charts.default.location.legend.options.verticalAlign;')
        self.assertEqual(
            new_state,
            'middle',
            msg='Legend middle align failed to set legend vertical align value'
        )
        self.browser.find_element_by_id('legend_bottom').click()
        new_state = self.browser.execute_script('return charts.default.location.legend.options.verticalAlign;')
        self.assertEqual(
            new_state,
            'bottom',
            msg='Legend bottom align failed to set legend vertical align value'
        )

        # Now we test the floating value
        self.browser.find_element_by_id('legend_float').click()
        new_state = self.browser.execute_script('return charts.default.location.options.legend.floating;')
        self.assertEqual(
            new_state,
            'true',
            msg="Floating button failed to set floating value"
        )

        # Now we test the layout options
        self.browser.find_element_by_id('legend_vert_layout').click()
        new_state = self.browser.execute_script('return charts.default.location.options.legend.layout;')
        self.assertEqual(
            new_state,
            'vertical',
            msg="Vertical Legend Layout button failed to set legend vertical layout value"
        )
        self.browser.find_element_by_id('legend_horiz_layout').click()
        new_state = self.browser.execute_script('return charts.default.location.options.legend.layout;')
        self.assertEqual(
            new_state,
            'horizontal',
            msg="Vertical Legend Layout button failed to set legend horizontal layout value"
        )
        self.browser.find_element_by_id('legend_rtl').click()
        new_state = self.browser.execute_script('return charts.default.location.options.legend.rtl;')
        self.assertEqual(
            new_state,
            'true',
            msg="Legend rtl button failed to toggle rtl value"
        )
