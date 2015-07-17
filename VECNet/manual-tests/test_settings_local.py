import os
import sys
import unittest


class SettingsLocalTests(unittest.TestCase):
    """
    Tests for settings_local module.
    """
    @classmethod
    def setUpClass(cls):
        # Add top-level project folder to the import search path
        this_script_folder = os.path.dirname(os.path.abspath(__file__))
        cls.VECNET_folder = os.path.dirname(this_script_folder)
        cls.project_folder = os.path.dirname(cls.VECNET_folder)
        sys.path.append(cls.project_folder)

        # Does settings_local.py exist?
        cls.settings_local_path = os.path.join(cls.VECNET_folder, 'settings_local.py')
        cls.settings_local_pyc = os.path.splitext(cls.settings_local_path)[0] + '.pyc'
        cls.settings_local_exists = os.path.exists(cls.settings_local_path)


    def test_app_env(self):
        """
        Test the assignment of APP_ENV in settings_local.
        """

        from VECNet import app_env

        if not self.settings_local_exists:
            print 'Creating "%s"...' % self.settings_local_path
            if os.path.exists(self.settings_local_pyc):
                os.remove(self.settings_local_pyc)  # Make sure a .pyc is generated for the .py file we're about to create
            f = file(self.settings_local_path, 'w')
            f.write('APP_ENV = "%s"' % app_env.QA)
            f.close()

        from VECNet import settings_local
        if self.settings_local_exists and not hasattr(settings_local, 'APP_ENV'):
            print 'Assigning settings_local.APP_ENV = "%s"...' % app_env.QA
            setattr(settings_local, 'APP_ENV', app_env.QA)

        # Try APP_ENV.is_production class method
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "VECNet.settings")
        from django.conf import settings
        self.assertTrue(isinstance(settings.APP_ENV, basestring))
        self.assertEqual(settings.APP_ENV, app_env.QA)
        self.assertTrue(app_env.is_qa())
        self.assertFalse(app_env.is_production())
        self.assertFalse(app_env.is_development())

    def tearDown(self):
        #  Clean up
        if not self.settings_local_exists:
            for path in (self.settings_local_path, self.settings_local_pyc):
                print 'Removing "%s"...' % path
                os.remove(path)


if __name__ == '__main__':
    unittest.main()