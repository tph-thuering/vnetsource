class Error(Exception):
    """
    Represents an error that occurs when interacting with job services.
    """

    def __init__(self, message, error_code=None):
        """
        Initialize a new instance.

        :param message: A message describing the error.
        :type  message: str

        :param error_code: A unique code that identifies the error.  Used when a single function can detect more than
                           one type of error.  A short string for readability when debugging.
        :type  error_code: str
        """
        self.message = message
        self.error_code = error_code

    def __str__(self):
        """
        Value returned when printing the object.
        """
        return self.message
