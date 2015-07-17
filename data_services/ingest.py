from data_services.ingesters.EMOD_ingest import EMOD_ingester

MODELS = {
    "EMOD": EMOD_ingester,
    "UNSPECIFIED": EMOD_ingester
}   #:


def ingest_files(zip_file, model_type, execid = None, seriesid = None):
    """
    This method accepts a path to a zip file and a model type and calls the appropriate ingester. It is responsible for
    determining which ingester to use, in order to abstract such functionality from the tools.
    :param File zip_file: A path to a file. The path should point to a zip file.
    :param string model_type: A string indicating the simulation model type.
    :return: None
    """
    # get the appropriate ingester using the model_type
    # if execution happens in ingest() or process_metadoc(), just propagate it to caller
    if model_type == "OM" or model_type == "OpenMalaria":
        raise NotImplementedError("OM Ingestion is no longer supported")
    else:
        tmp_ingester = MODELS[model_type](zip_file, execid=execid, seriesid=seriesid)
        tmp_ingester.ingest()

    return None
