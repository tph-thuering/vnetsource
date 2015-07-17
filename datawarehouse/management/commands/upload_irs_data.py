__author__ = 'Alexander'

from datawarehouse.models import LutInterventionItnCoveragesAdmin1, LutInterventionIrsCoveragesAdmin1
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
            irsdata = csv.reader(csvfile, delimiter=",")
            for row in irsdata:
                print row[1], row[0]
                #print ".%s." % float(row[4])
                irs = LutInterventionIrsCoveragesAdmin1()
                irs.gaul_code = int(row[0])
                irs.country = row[2]
                irs.province_name = row[1]
                try:
                    irs.percent_of_the_population_protected_by_irs = float(row[3])
                except ValueError:
                    irs.percent_of_the_population_protected_by_irs = None

                try:
                    irs.year = int(row[4])
                except ValueError:
                    print "ValueError: Year"
                    continue
                try:
                    irs.source = row[5]
                except ValueError:
                    print "ValueError: source"
                    continue
                irs.save()
        print options
        pass