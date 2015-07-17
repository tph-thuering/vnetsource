from django.core.exceptions import ImproperlyConfigured


class ConfigurationError(ImproperlyConfigured):
    """
    Represents an error that occurs when configuring job services.
    """

    def __init__(self, message, error_code=None):
        """
        Initialize a new instance.

        :param message: A message describing the error.
        :type  message: str

        :param error_code: A unique code that identifies the error.  Used when a single function can detect more than
                           one type of configuration error.  A short string for readability when debugging.
        :type  error_code: str
        """
        self.message = message
        self.error_code = error_code

    def __str__(self):
        """
        Value returned when printing the object.
        """
        return self.message


class ConfigurationErrorCodes(object):
    """
    Error codes that can be thrown by any module.
    """
    SETTINGS_TYPE = 'settings: wrong type'
