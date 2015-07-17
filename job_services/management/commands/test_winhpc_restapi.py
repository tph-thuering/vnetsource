import time

from django.core.management.base import BaseCommand, CommandError

from job_services.providers.winhpc.third_party import winhpclib
from VECNet.secrets_default import NotreDameWindows


class Command(BaseCommand):
    """
    Integration test to check if app-server code can interact with a Windows HPC server via its REST API.
    """
    help = 'Test the Windows HPC REST API for ND dev cluster'

    def handle(self, *args, **options):
        if len(args) > 0:
            raise CommandError("Unexpected arguments: %s" % ' '.join(args[1:]))

        print "Configuring connection to server:", NotreDameWindows.SERVER
        server = winhpclib.Server(NotreDameWindows.SERVER, NotreDameWindows.USERNAME, NotreDameWindows.PASSWORD)

        job = winhpclib.Job(server)
        job.properties["FailOnTaskFailure"] = "True"
        job.properties["Name"] = "Test WinHPC REST API"
        job.properties["Priority"] = "Normal"
        job.create()
        print "Created job %d on the server" % job.id

        echo_args = ('uno_1', 'Dos.2', 'TRES/3')
        task = job.create_task()
        task.properties["Commandline"] = r'C:\Windows\system32\cmd.exe /c echo %s' % ' '.join(echo_args)
        task.properties["Name"] = "Echo arguments"
        task.properties["WorkDirectory"] = r'C:\\'
        task.create()
        print "Created task %d on the server" % task.task_id

        job.submit( NotreDameWindows.USERNAME, NotreDameWindows.PASSWORD )
        print "Job %d submitted to server" % job.id

        job_terminated = False
        while not job_terminated:
            time.sleep(1)
            job.refresh_properties()
            job_state = job.properties["State"]
            print "Job %d : %s" % (job.id, job_state)
            if job_state in ("Canceled", "Failed", "Finished"):
                job_terminated = True

        task.refresh_properties()
        task_output = task.properties["Output"].rstrip()
        print 'Task %s output : "%s"' % (task.task_id, task_output)
        expected_output = ' '.join(echo_args)
        if task_output == expected_output:
            print 'Test passed'
        else:
            raise CommandError('Test failed: expected task output = "%s"' % expected_output)