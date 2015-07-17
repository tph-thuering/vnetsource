"""
This contains the router for AutoScotty.  To ensure that multiple instance of AutoScotty can run, the
database backend for AutoScotty should be a local sqlite databse.  This is the router to ensure that
the models for AutoScotty (namely those for djcelery) live only in the sqlite DB.
"""
__author__ = 'lselvy'

APPS_USING_SQLITE = set(['djcelery'])
"""
The set of Django applications that have their data models in a local sqlite database.
"""


class AS_Router(object):
    """
    This will ensure that the models from app 'djcelery' are router appropriately to the sqlite
    database
    """

    def db_for_read(self, model, **hints):
        """
        This defines which database to use for purposes of reading data.

        We explicitly set the djcelery application to go to the sqlite database.
        """
        if model._meta.app_label in APPS_USING_SQLITE:
            return 'sqlite'
        else:
            return 'default'

    def db_for_write(self, model, **hints):
        """
        This defines which database to use for purposes of writing data.

        Here we explicitly set the djcelery application to go to the sqlite database.
        """
        if model._meta.app_label in APPS_USING_SQLITE:
            return 'sqlite'
        else:
            return 'default'

    def allow_syncdb(self, db, model):
        """
        This defines how to use syncdb with the sqlite database.

        If the database alias passed in is sqlite, only sync the djcelery models.  Otherwise if
        the model is a djcelery model, don't sync it.  (Ensures djcelery only syncs to sqlite).
        """
        if db == 'sqlite':
            return model._meta.app_label in APPS_USING_SQLITE
        elif model._meta.app_label in APPS_USING_SQLITE:
            return False
        return None