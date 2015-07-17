from django.conf import settings
from ..base import ProviderBase
from ...api import Status
import logging
import json
import datetime
from data_services.manifestPreproc import manifest_preprocessor
from job_services.providers.winhpc.winhpc_submit import winhpc_submit
from VECNet import app_env
from data_services import emod_id
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('prod_logger')


class WinHpcManifestProvider(ProviderBase):
    """
    A provider for the WinHpc cluster and the EMOD simulation model that utilizes manifest files.
    """
    def __init__(self, definition, run, user):
        super(WinHpcManifestProvider, self).__init__(definition, run, user)

    def get_run_status(self):
        """
        Returns a status object containing information about the job.
        """
        n_reps = 0
        failed_reps = 0
        finished_reps = 0
        for execution in self.run.dimexecution_set.all():
            for replication in execution.dimreplication_set.all():
                n_reps += 1
                if replication.status == 0:
                    finished_reps += 1
                elif replication.status == 1:
                    failed_reps += 1
        status = Status(n_replications=n_reps, completed_replications=finished_reps, failed_replications=failed_reps)
        return status

    def submit_jobs(self, reps_per_exec):
        """
        Submits a job to the WinHPC cluster for processing. Returns True if submission was successful, and False if it
        wasn't.
        :returns: Boolean
        """
        # check that the run produces a valid manifest
        validate_manifest(self.run, reps_per_exec)

        # check if the environment is production or not
        production = app_env.is_production()

        # retrieve the ingestion url
        #TODO have ingestion url always set in settings, and/or have ingestion url be configurable
        ingest_url = (settings.INGESTION_URL if hasattr(settings, 'INGESTION_URL') else "")
        #TODO this type checking should be done in settings
        if not isinstance(ingest_url, (str, unicode)):
            raise TypeError("INGESTION_URL in settings must be a string or unicode")
        secrets_dict = {
            "host": self.cluster.server,
            "password": self.cluster.password,
            "username": self.cluster.username
        }

        # base_dir = getattr(settings, "JOB_SERVICES_BASE_DIR", None)
        # status = psc_submit_manifest(str(self.run.id),
        #                              self.user.username,
        #                              secrets_dict,
        #                              use_prod_site=production,
        #                              alt_ingest_url=ingest_url,
        #                              base_dir=base_dir)
        if self.run.model_version == emod_id.EMOD15:
            script_path = getattr(settings, "JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH", None)
            if script_path is None:
                raise ImproperlyConfigured("JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH_EMOD is not configured")
        elif self.run.model_version == emod_id.EMOD161: # or self.run.model_version == emod_id.EMOD167
            script_path = getattr(settings, "JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH_EMOD_161", None)
            if script_path is None:
                raise ImproperlyConfigured("JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH_EMOD_161 is not configured")
        elif self.run.model_version == emod_id.EMOD167: # or self.run.model_version == emod_id.EMOD167
            script_path = getattr(settings, "JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH_EMOD_167", None)
            if script_path is None:
                raise ImproperlyConfigured("JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH_EMOD_167 is not configured")
        elif self.run.model_version == emod_id.EMOD18: # or self.run.model_version == emod_id.EMOD167
            script_path = getattr(settings, "JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH_EMOD_18", None)
            if script_path is None:
                raise ImproperlyConfigured("JOB_SERVICES_START_SIMGROUP_SCRIPT_PATH_EMOD_18 is not configured")
        else:
            raise RuntimeError("Unsupported model version %s (DimRun %s)" % (self.run.model_version, self.run.id))

        status = winhpc_submit(self.run.id,
                               self.user.username,
                               script_path,
                               secrets_dict["host"],
                               secrets_dict["username"],
                               secrets_dict["password"],
                               ingest_url # To be replaced with ALT_INGEST_URL
                               )


        if status == -1:
            logger.error("Run %s was not launched, received -1 from submit method" % self.run.id )
            return False
        logger.info("Run %s was launched successfully" % self.run.id)
        self.run.time_launched = datetime.datetime.now()
        self.run.save()
        return True


def validate_manifest(run, reps_per_exec):
    try:
        manifest = manifest_preprocessor(run, reps_per_exec=reps_per_exec)
        mjson = manifest.as_json()
        mdict = json.loads(mjson)
    except Exception as e:
        logger.error("Run %s has encountered an error:\n\t%s" % (run.id, e.message))
        raise Exception("An exception has occurred:\n\t%s" % e.message)