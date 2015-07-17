"""
Names of job-service providers
"""

#: Prototype provider that uses non-manifest job submission in EMOD model adapter
PROTOTYPE = 'prototype'

#: Prototype provider for manifest-based job submission for EMOD simulations
MANIFEST_PROTOTYPE = 'manifest prototype'


class TestingApi(object):
    """
    API for unit tests.
    """
    MOCK_NAME = "(mock)"