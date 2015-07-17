from .. import clusters


class ProviderDefinition(object):
    """
    Definition of a provider of job services.
    """
    def __init__(self, name, cluster, simulation_model, aux_params=None):
        if aux_params is None:
            aux_params = {}
        assert isinstance(aux_params, dict)
        self.name = name
        self.cluster = cluster
        assert isinstance(cluster, clusters.Cluster)
        self.simulation_model=simulation_model
        self.aux_params = aux_params