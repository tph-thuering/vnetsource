DEVELOPMENT = "dev"
QA = "qa"
PRODUCTION = "production"
ALL_KNOWN = (DEVELOPMENT, QA, PRODUCTION)

_app_env = None


def set(app_env):
    """
    Set the application environment.

    :param str app_env: One of the string constants defined above.
    :returns bool: True if the application environment is valid; False if it's invalid.
    """
    if app_env in ALL_KNOWN:
        global _app_env
        _app_env = app_env
        return True
    else:
        return False


def is_production():
    """
    Is the application running in a production environment?
    """
    return _app_env == PRODUCTION


def is_qa():
    """
    Is the application running in a QA environment?
    """
    return _app_env == QA


def is_development():
    """
    Is the application running in a development environment?
    """
    return _app_env == DEVELOPMENT
