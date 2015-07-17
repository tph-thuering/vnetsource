"""
Here we test the manifest package by instantiating a ManifestFile in all three ways it can be instantiated, and test
the functionality of all object/static/class methods.
"""

__author__ = 'lselvy'

from manifest.manifest import ManifestFile, Slug
import unittest
import random

class TestSlug(unittest.TestCase):
    """
    Here we test the slug class, to make sure that it can create objects correctly from dictionaries.
    """

    def setUp(self):
        """
        Here we build the dictionary required to feed into a Slug and see if those attributes exist.
        """
        self.slug1 = dict()     #: Ths first slug
        for x in range(0, 10):
            self.slug1[str(random.randint(0, 1E16))] = random.random()

        self.slug2 = dict()     #: The second slug, testing immutable types like dictionaries and lists
        self.slug2['list1'] = [1, 2, 3, 4, 5]
        self.slug2['tuple1'] = (1, 2, 3, 4)
        self.slug2['dict1'] = self.slug1

    def testImmutableTypes(self):
        """
        Here we test how the slug class deals with immutable types.

        We will use slug1 for this.
        """
        slug1 = Slug(**self.slug1)

        for key, value in self.slug1.iteritems():
            self.assertTrue(
                hasattr(slug1, key),
                msg="Slug did not create key %s" % key
            )
            self.assertEqual(
                getattr(slug1, key),
                value,
                msg="Slug object was not transformed from dictionary correctly.  Expected value %(val)s received %(slug)s" %
                    {
                        'val': value,
                        'slug': getattr(slug1, key)
                    }
            )

    def testMutableTypes(self):
        """
        Here we test how the slug class deals with mutable types.

        To do this we will yse slug2.
        """
        slug = Slug(**self.slug2)

        self.assertTrue(
            hasattr(slug, 'list1'),
            msg="List type was not created in slug"
        )
        self.assertEqual(
            slug.list1,
            self.slug2['list1'],
            msg="Slug list type was not created correctly, lists mismatched"
        )

        self.assertTrue(
            hasattr(slug, 'tuple1'),
            msg="Tuple type was not created in slug"
        )
        self.assertEqual(
            slug.tuple1,
            self.slug2['tuple1'],
            msg="Slug tuple type was not created correctly, tuples mismatched"
        )

        self.assertTrue(
            hasattr(slug, 'dict1'),
            msg="Slug dictionary was not created in slug"
        )
        self.assertEqual(
            slug.dict1,
            self.slug2['dict1'],
            msg="Slug dictionary was not created correctly, dictionaries mismatched"
        )


class TestBuildManifest(unittest.TestCase):
    """
    Here we test all the methods of the ManifestFile class.
    """

    def setUp(self):
        """
        Here we setup the slug objects we are going to use to test the ManifestFile

        These include 3 executions, 2 Run objects, 3 Template Objects that are functional and
        1 execution and 1 run object that is not.
        """
        self.run1 = Slug(**{
            'id': random.randint(0,1E16),
            'base_changes': ''
        })

        self.run2 = Slug(**{
            'id': random.randint(1E16 + 1, 1E17),
            'base_changes': 'chang1_place_holder'
        })

        self.bad_run = Slug(**{
            'not_id': 'Not id',
            'base_changes': 'To bad for runs'
        })

        self.exec1 = Slug(**{
            'name': 'Execution1',
            'id': random.randint(0, 1E16),
            'replications': 10,
            'xpath_changes': ''
        })

        self.exec2 = Slug(**{
            'name': 'Execution2',
            'id': random.randint(0, 1E16),
            'replications': 10,
            'xpath_changes': 'changes_place_holder'
        })

        self.bad_exec = Slug(**{
            'not_id': 'Not id',
            'replications': 10,
            'name': 'Bad Execution',
            'xpath_changes': 'Bad to the bone'
        })

        self.exec3 = Slug(**{
            'name': 'Execution3',
            'id': random.randint(0, 1E16),
            'replications': 10,
            'xpath_changes': 'changes_place_holder'
        })

        self.template_config = "This is a config template"
        self.template_campaign = "This is a campaign template"
        self.template_input = "This is an input template"

    def testManifestFromEmpty(self):
        """
        This tests the ManifestFile functionality from scratch.
        """
        manifest = ManifestFile()

        #------ Adding bad run
        self.assertRaises(
            TypeError,
            manifest.add_run,
            self.bad_run
        )

        manifest.add_run(self.run1)

        self.assertEqual(
            manifest.run,
            self.run1,
            msg="Run was not added correctly"
        )

        #------ Here we test to make sure only one run can be added and it fails silently
        #------ if a run is already in place.  Also checking to make sure the run is not
        #------ overwritten.

        manifest.add_run(self.run2)

        self.assertNotEqual(
            manifest.run,
            self.run2,
            msg="Run was overwritten"
        )

        #------ Adding single executions
        manifest.add_execution(self.exec1)

        self.assertIn(
            self.exec1,
            manifest.executions,
            msg="Failed to add single execution"
        )

        #------ Adding list of executions
        manifest.add_execution([self.exec2, self.exec3])

        self.assertIn(
            self.exec2,
            manifest.executions,
            msg="Failed to add list execution"
        )

        self.assertIn(
            self.exec3,
            manifest.executions,
            msg="Failed to add list execution"
        )

        #------ Adding bad execution
        self.assertRaises(
            TypeError,
            manifest.add_execution,
            self.bad_exec,
        )

        #------ Adding single template
        manifest.add_template('input', self.template_input)

        self.assertIn(
            'input',
            manifest.templates,
            msg="Failed to add input to templates"
        )

        self.assertEqual(
            manifest.templates['input'],
            self.template_input,
            msg="Failed to add correct content to input in templates"
        )

        #------ Adding templates by lists
        manifest.add_template(['config', 'campaign'], [self.template_config, self.template_campaign])

        self.assertIn(
            'config',
            manifest.templates,
            msg="Failed to add config to templates"
        )

        self.assertEqual(
            manifest.templates['config'],
            self.template_config,
            msg="Failed to add correct content to config in templates"
        )

        self.assertIn(
            'campaign',
            manifest.templates,
            msg="Failed to add campaign to templates"
        )

        self.assertEqual(
            manifest.templates['campaign'],
            self.template_campaign,
            msg="Failed to add correct content to campaign in templates"
        )

    def testManifestFromInstantiation(self):
        """
        Here we check to see if the manifest is correctly created when instantiated
        with objects.
        """
        self.assertRaises(
           TypeError,
           ManifestFile,
           run=self.bad_run,
        )

        manifest = ManifestFile(run=self.run1)

        self.assertEqual(
            manifest.run,
            self.run1,
            msg="Failed to create object with run"
        )

        manifest.add_run(self.run2)

        self.assertNotEqual(
            manifest.run,
            self.run2,
            msg="Run was overwritten"
        )