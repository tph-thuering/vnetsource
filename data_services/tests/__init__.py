from model_adapter_tests import *
from file_system_storage_test import FileSystemStorageTest
#from ingester_tests import *  # comment out
from pg_utils_tests import *
#from data_services.data_api.tests import *  # comment out
#from .sim_file_server.tests import *  # comment out
from .sim_file_server.tests import DataSchemeServerTests, FileSchemeServerTests, FileSchemeConfTests    ,DataSchemeHandlerTests    ,MultiSchemeTestsThatWriteDataScheme    ,FileSchemeHandlerTests    ,ServerConfTests    ,MultiSchemeTestsThatWriteFileScheme    ,HttpsSchemeConfTests    ,HttpsSchemeHandlerTests    ,HttpsSchemeHandlerAuthTests    ,HttpsSchemeServerTestsNoAuth    ,HttpsSchemeServerTestsWithAuth    ,MultiSchemeTestsThatWriteHttpsScheme
from .input_file_tests import *
from .output_file_tests import *
from .rest_api_tests import *
#from .run_data_tests import *  # comment out
from .sim_data_model_tests import *
#from .data_services_models_tests import *  # comment out