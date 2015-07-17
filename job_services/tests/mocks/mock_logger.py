class MockLogger(object):
    """
    A mock object for a python logging.logger.
    """
    def __init__(self, name):
        self.name = name
        self.errors = list()

    def error(self, message):
        """
        Add an error message to self.errors.
        """
        self.errors.append(message)

def get_logger(name):
    return MockLogger(name)