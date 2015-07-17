from django.core.management.base import NoArgsCommand
from data_services.adapters import EMOD_Adapter
from data_services.models import *
import time
import sys

class Command(NoArgsCommand):
    allowed_locations=dict()
    available_runs=dict()

    def handle(self, *args, **options):
        if len(args)==1 and "-h"==args[0]:
            print "Usage: test_locations"
            sys.exit(0)



        tstart = time.time()
        run = DimRun.objects.get(id = 1509)
        number = len(run.dimexecution_set.all())
        print "%s executions to go" % number
        adapter = EMOD_Adapter("admin")
        i = 0
        for execution in run.dimexecution_set.all():
            adapter.fetch_data(execution.id, channel_name="Daily EIR")
            i += 1
            print "%s / %s (%s)" % (i, number, time.time() - tstart)

        tend = time.time()
        print "timing: fetch_data from run 1509 took %f sec" % (tend-tstart)
