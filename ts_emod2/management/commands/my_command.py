__author__ = 'Alexander'

from django.core.management.base import BaseCommand
from data_services.models import Simulation

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
            print "Please specify filename 123"
            exit(0)
        filename = args[0]
        print "Hello, world!"