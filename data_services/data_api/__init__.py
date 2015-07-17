"""
This is the data_api module.

This will act as a layer of abstraction between the ORM and the code.  This API will wrap some, not all,
classes in the models file to add functionality for the CI.
"""

from baseline import *
from emod_baseline import EMODBaseline
from data_services.models import DimModel


def get_baseline(model):
    """
    This serves as the factory method for the baselines.  Given a name or DimModel object, this
    will return the appropriate scenario.

    :param model: Model for which scenario to get
    :type model: str or DimModel
    :returns: EMODBaseline
    :raises: ValueError when model is neither string or DimModel instance, NotImplemented if the model that is passed
            in does not have a Baseline object.
    """
    if isinstance(model, DimModel):
        model = model.model
    else:
        if not isinstance(model, (str, unicode)):
            raise ValueError("Model name or string is required to fetch appropriate scenario")

    model = model.lower().strip()

    baseline_types = {
        'emod': EMODBaseline
    }

    if model not in baseline_types.keys():
        raise NotImplementedError("A Baseline for model %s has not been implemented")

    return baseline_types.get(model, None)