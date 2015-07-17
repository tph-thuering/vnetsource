import data_services
import data_services.ingest
from celery import Celery
from celery.utils.log import get_task_logger
from django.core.mail import send_mail
from django.conf import settings
import traceback

logger = get_task_logger(__name__)
BROKER_URL = getattr(settings, "BROKER_URL", 'amqp://guest@localhost//')

celery = Celery('tasks', backend='amqp', broker=BROKER_URL)


@celery.task
def ingest_files(path_to_file, model_type, execid=None, seriesid=None):
    """
    This method is a celery task responsible for ingesting files. It accepts a path to a zip file, and a simulation
    model type, and it calls the appropriate data services ingestion methods.
    :param string path_to_file: A path to a zip_file containing the files to be ingested.
    :param string model_type: A string indicating the simulation model type.
    :return: Null
    """
    logger.info("Running ingestion scripts.")
    logger.info("Filename: %s, execid: %s, seriesid: %s", path_to_file, execid, seriesid)
    # make sure the file path is a string or unicode, mainly to ensure file objects aren't being passed
    if not isinstance(path_to_file, (str, unicode)):
        raise TypeError("path_to_file must be of type string or unicode, but is of type %s" % type(path_to_file))
    try:
        data_services.ingest.ingest_files(path_to_file, model_type, execid, seriesid)
    except:
        stacktrace = traceback.format_exc()
        #traceback.print_exc()
        print stacktrace
        #traceback.print_tb(stacktrace)
        send_mail('Ingestion Failure', "An %s ingestion failed. The path is %s\n%s" % (model_type, path_to_file, stacktrace),
                  settings.SERVER_EMAIL,
                  [r[1] for r in settings.ADMINS])
