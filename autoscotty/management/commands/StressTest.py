import requests
import shutil
import hashlib
import os
from data_services.models import DimChannel, DimRun, DimExecution, DimReplication, BaseFactData
from multiprocessing import Process
from django.core.management.base import BaseCommand
from optparse import make_option


class Command(BaseCommand):
    """
    Stress tests management command for AutoScotty. ONLY WORKS WITH EMOD AND THE TEST FILE LOCATED IN THIS FOLDER.
    """
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
        make_option('--numrequest',
                    action='store',
                    type="int",
                    dest='number_of_requests',
                    default=False,
                    help='The number of requests to send for the stress test. Defaults to 100.'),

    )

    def handle(self, *args, **options):
        """
        Main function for the management command. Submits several AutoScotty requests in parallel.
        """
        self.model_input = []
        self.file_names = []
        processes = []
        num_requests = options['number_of_requests'] if options['number_of_requests'] else 100

        for i in range(0, num_requests):
            rep = self.create_structure()
            tmp_file_name = self.create_tmp_file(options['filename'], rep)

            with open(tmp_file_name, 'rb') as f:
                if options['hashname']:
                    hashname = options['hashname']
                else:
                    myhash = hashlib.sha1()
                    myhash.update(f.read())
                    f.seek(0)
                    hashname = myhash.hexdigest()

                files = {'zip_file': f}
                urlname = options['urlname']
                model_type = options['modeltype']
                p = Process(target=self.submit_request, args=(urlname, model_type, hashname, files))
                processes.append(p)
                p.start()

        # wait for all processes to finish before purging data
        for p in processes:
            p.join()
        self.remove_data()

    def create_structure(self):
        """
        Creates the necessary model input data in the database to ingest against.
        :return: An integer representing the replication created.
        """
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

        self.model_input.append([myrun.id, myex.id, myrep.id, mychannel.id])

        return myrep.id

    def remove_data(self):
        """
        Remove the temporary model input data and the temporary files.
        :return: Null
        """
        for item in self.file_names:
            os.remove(item)

        for item in self.model_input:
            tmp_run = DimRun.objects.get(id=item[0])
            tmp_rep = DimReplication.objects.get(id=item[2])
            tmp_ex = DimExecution.objects.get(id=item[1])
            tmp_channel = DimChannel.objects.get(id=item[3])

            BaseFactData.objects.filter(replication_key_id=tmp_rep.id, channel_key_id=item[3],
                                        run_key_id=tmp_run.id).delete()
            tmp_run.dimchannel_set.remove(tmp_channel.id)
            tmp_rep.delete()
            tmp_ex.delete()
            tmp_run.delete()

    def submit_request(self, urlname, model_type, hashname, files):
        """
        Submits a request. Used by handle.
        """
        r = requests.post(urlname, files=files, data={'model_type': model_type,
                                                      'sync': True,
                                                      'zip_file_hash': hashname})
        print r.status_code

    def create_tmp_file(self, original_file_name, replication_number):
        """
        Create a temporary file that is a copy of the original.
        :param string original_file_name: The name of the file from the command line.
        :param int replication_number: The replication number for the file.
        :return: A string containing the name of the new file.
        """
        oldfilename = original_file_name
        oldlist = oldfilename.split(".")
        newfilename = oldlist[0] + "-" + str(replication_number) + "." + oldlist[1]
        shutil.copyfile(original_file_name, newfilename)
        self.file_names.append(newfilename)
        return newfilename