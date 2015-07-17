__author__ = 'Alexander'

from datawarehouse.models import LutInterventionItnCoveragesAdmin1
from django.core.management.base import BaseCommand
import csv

class Command(BaseCommand):
    """
    This class defines the ETL command. The ETL command is used
    to ingest data given an input file and a mapping file. It is
    important to note that location is hardcoded due to the complicated
    nature of gis data. The rest of the class is dynamic and could be
    easily reused in other projects.
    """


    def handle(self, *args, **options):
        """This method is responsible for 'handling' the inputs.

        This method is the heart of the management command.
        It uses the given inputs, along with other methods, to ingest
        data.

        :param *args: Argument list.
        :param **options: Command line options list.
        """
        if len(args) == 0:
            print "Please specify filename"
            exit(0)
        filename = args[0]
        with open(filename, 'rb') as csvfile:
            itndata = csv.reader(csvfile, delimiter=",")
            for row in itndata:
                print row[1], row[0]
                #print ".%s." % float(row[4])
                itn = LutInterventionItnCoveragesAdmin1()
                itn.gaul_code = int(row[0])
                itn.country = row[2]
                itn.province_name = row[1]
                try:
                    itn.percent_of_children_under_5_years_sleeping_under_a_bednet = float(row[4])
                except ValueError:
                    itn.percent_of_children_under_5_years_sleeping_under_a_bednet = None

                try:
                    itn.the_estimated_percent_households_with_itn= float(row[5])
                except ValueError:
                    itn.the_estimated_percent_households_with_itn = None

                try:
                    #print float(ronow[6])
                    itn.percent_itn_all = float(row[6])
                    #print "itn_all_good"
                except ValueError:
                    #print "itn_all"
                    itn.percent_itn_all = None
                try:
                    itn.year = int(row[7])
                except ValueError:
                    continue
                try:
                    itn.source = row[8]
                except ValueError:
                    continue
                itn.save()
        print options
        pass