import requests
import os
import hashlib
import shutil
from data_services.models import DimChannel, DimRun, DimExecution, DimReplication, BaseFactData
from django.core.management.base import BaseCommand
from optparse import make_option
from django.db.models import Count


class Command(BaseCommand):
    # TODO Add class docstring
    option_list = BaseCommand.option_list + (
        make_option('--file',
                    action='store',
                    type="string",
                    dest='filename',
                    default=False,
                    help='The input file.'),
        make_option('--url',
                    action='store',
                    type="string",
                    dest='urlname',
                    default=False,
                    help='The input file.'),
        make_option('--hash',
                    action='store',
                    type="string",
                    dest='hashname',
                    default=False,
                    help='The hash for the input file.'),
        make_option('--model',
                    action='store',
                    type="string",
                    dest='modeltype',
                    default=False,
                    help='The simulation model type (e.g. EMOD).'),
    )

    def handle(self, *args, **options):
        print "BEGIN TEST"
        # Create execution, replication, and run
        myrun = DimRun()
        myrun.name = "AUTO SCOTTY TEST RUN"
        myrun.models_key_id = 1
        myrun.save()

        mychannel = DimChannel.objects.get(pk=228441)
        myrun.dimchannel_set.add(mychannel)

        myex = DimExecution()
        myex.run_key_id = myrun.id
        myex.save()

        myrep = DimReplication()
        myrep.execution_key_id = myex.id
        myrep.seed_used = 99
        myrep.series_id = 100
        myrep.save()

        replication_number = myrep.id
        print "REPLICATION NUMBER", replication_number
        print "CHANNEL NUMBER", mychannel.id
        print "RUN NUMBER", myrun.id
        print "EXECUTION NUMBER", myex.id
        # rename the test zip_file
        oldfilename = options['filename']
        oldlist = oldfilename.split(".")
        newfilename = oldlist[0] + "-" + str(replication_number) + "." + oldlist[1]
        shutil.copyfile(oldfilename, newfilename)
        # make sure this replication output data doesn't already exist
        results = [i for i in BaseFactData.objects.filter(replication_key_id=replication_number,
                                                          channel_key_id=mychannel.id, run_key_id=myrun.id)]
        count = len(results)
        if count != 0:
            print "There currently exists data in BaseFactData for the chosen replication, channel, and run." \
                  "Please choose a replication, channel, and run which have not previously been ingested."

        # Curl the files to AutoScotty
        print "Beam us up, Scotty.\nAye, Sir."
        print "File: ", newfilename
        f = open(newfilename, 'rb')
        files = {'zip_file': f}
        urlname = options['urlname']
        model_type = options['modeltype']
        if options['hashname']:
            r = requests.post(urlname, files=files, data={'model_type': model_type, 'sync': True,
                                                          'zip_file_hash': options['hashname']})
        else:
            myhash = hashlib.sha1()
            myhash.update(f.read())
            f.seek(0)
            r = requests.post(urlname, files=files, data={'model_type': model_type, 'sync': True,
                                                          'zip_file_hash': myhash.hexdigest()})

        # remove the temporary copy of the file
        os.remove(newfilename)

        if r.status_code != 200:
            print "There was an ingestion error at the server. The HTTP Response code is: ", r.status_code
            print "Please check the celery and apache logs on the server to determine the source of the error."

        # fetch the ingested results
        results = BaseFactData.objects.filter(replication_key_id=replication_number, channel_key_id=mychannel.id,
                                              run_key_id=myrun.id).aggregate(Count("timestep"))
        count = results['timestep__count']

        if count == 10950:
            print "The anticipated number of entries in BaseFactData were present. The data was successfully ingested."
        else:
            print "The count of " + str(count) + " is not the expected number of entries. Please make sure channel " \
                                                 "228441 exists, and that you used the 'autoscottytest.zip' file."

        # remove the ingested data
        BaseFactData.objects.filter(replication_key_id=replication_number, channel_key_id=mychannel.id,
                                    run_key_id=myrun.id).delete()
        myrun.dimchannel_set.remove(mychannel)
        myrep.delete()
        myex.delete()
        myrun.delete()

        # make sure data was deleted
        results = BaseFactData.objects.filter(replication_key_id=replication_number, channel_key_id=mychannel.id,
                                              run_key_id=myrun.id).aggregate(Count("timestep"))
        count = results['timestep__count']
        if count == 0:
            print "The data was successfully purged."
        else:
            print "There was an error removing the ingested data.  There are still entries in BaseFactData " \
                  "corresponding to your replication, channel, and run. Please see the server logs and the database " \
                  "administrator for assistance."

        # return response
        print "Live long and prosper."
