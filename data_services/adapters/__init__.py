########################################################################################################################
# VECNet CI - Prototype
# Date: 4/5/2013
# Institution: University of Notre Dame
# Primary Authors:
########################################################################################################################

# These are the data adapters and data adapter related materials for the VECNet CI

from EMOD import *
from OM import *
from model_adapter import *

get_model_adapter = {
    'EMOD': EMOD_Adapter,
    'Open Malaria': OM_Adapter
}
