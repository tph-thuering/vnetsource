import os
import shutil


class OutputDirMixin(object):
    """
    A mixin for test suites that need to create files on the local file system.  They are created in the test
    output directory, i.e., "./output/".
    """
    _output_dir = None

    @classmethod
    def get_output_dir(cls):
        """
        Get the full path to the test output directory.
        """
        if cls._output_dir is None:
            this_file = os.path.abspath(__file__)
            this_dir = os.path.dirname(this_file)
            cls._output_dir = os.path.join(this_dir, 'output')
        return cls._output_dir

    @classmethod
    def clean_output_dir(cls):
        """
        Remove all the files and subdirectories in the test output directory, so it doesn't continually fill up.
        """
        test_output_dir = cls.get_output_dir()
        for name in os.listdir(test_output_dir):
            item_path = os.path.join(test_output_dir, name)
            if os.path.isfile(item_path):
                os.remove(item_path)
            else:
                shutil.rmtree(item_path)


class DataDirMixin(object):
    """
    A mixin for test suites that need to access test files in the "data" directory.
    """
    _data_dir = None

    @classmethod
    def get_data_dir(cls):
        """
        Get the full path to the test data directory.
        """
        if cls._data_dir is None:
            this_file = os.path.abspath(__file__)
            this_dir = os.path.dirname(this_file)
            cls._data_dir = os.path.join(this_dir, 'data')
        return cls._data_dir


class OpenMalariaData:
    """
    Shared OpenMalaria test data.
    """

    CTSOUT_TXT_LINES = (
        "##\t##",
        "timestep\tsimulated EIR",
        "0\t0.273542",
        "1\t0.179792",
    )

    CTSOUT_TXT = '\n'.join(CTSOUT_TXT_LINES)

    EMPTY_SCENARIO_LINES = (
        "<?xml version='1.0' encoding='UTF-8' standalone='no'?>",
        "<om:scenario xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'",
        "    name='name'",
        "    schemaVersion='32'",
        "    xsi:schemaLocation='http://openmalaria.org/schema/scenario_32 scenario_32.xsd'",
        "    xmlns:om='http://openmalaria.org/schema/scenario_32'",
        "    analysisNo='0'",
        "    wuID='0'>",
        "</om:scenario>",
    )
    EMPTY_SCENARIO = '\n'.join(EMPTY_SCENARIO_LINES)
