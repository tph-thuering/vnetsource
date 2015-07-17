import unittest
from .. import model_id


class ModelIdTests(unittest.TestCase):
    """
    Unit tests for model_id module.
    """

    def test_max_length(self):
        """
        Verify that all known id constants fit within the maximum length.
        """
        for id_ in model_id.ALL_KNOWN:
            self.assertTrue(len(id_) <= model_id.MAX_LENGTH)

    def test_is_valid_with_all_known(self):
        """
        Test the is_valid function with each of the known id constants.
        """
        for id_ in model_id.ALL_KNOWN:
            self.assertTrue(model_id.is_valid(id_))

    def test_is_valid_with_bad_ids(self):
        """
        Test the is_valid function with bad ID strings.
        """
        self.assertFalse(model_id.is_valid("foo"))
        self.assertFalse(model_id.is_valid(u"foo"))
        self.assertFalse(model_id.is_valid(""))

    def test_is_valid_with_wrong_type(self):
        """
        Test the is_valid function with wrong data types.
        """
        self.assertRaises(TypeError, model_id.is_valid, None)
        self.assertRaises(TypeError, model_id.is_valid, 7)
        self.assertRaises(TypeError, model_id.is_valid, dict())
        self.assertRaises(TypeError, model_id.is_valid, model_id.ALL_KNOWN)

    def test_parse(self):
        """
        Test the parse function.
        """
        self.assertEqual(model_id.parse(" EMOD "), model_id.EMOD)
        self.assertEqual(model_id.parse("EMOD "), model_id.EMOD)
        self.assertEqual(model_id.parse(u" EMOD"), model_id.EMOD)
        self.assertEqual(model_id.parse(u"emod "), model_id.EMOD)
        self.assertEqual(model_id.parse(" emod"), model_id.EMOD)
        self.assertEqual(model_id.parse(" emod "), model_id.EMOD)
        self.assertEqual(model_id.parse(model_id.EMOD), model_id.EMOD)

        self.assertEqual(model_id.parse("OM"), model_id.OPEN_MALARIA)
        self.assertEqual(model_id.parse("OM  "), model_id.OPEN_MALARIA)
        self.assertEqual(model_id.parse("  OM  "), model_id.OPEN_MALARIA)
        self.assertEqual(model_id.parse("  OM"), model_id.OPEN_MALARIA)
        self.assertEqual(model_id.parse("om"), model_id.OPEN_MALARIA)
        self.assertEqual(model_id.parse("om  "), model_id.OPEN_MALARIA)
        self.assertEqual(model_id.parse("  Om  "), model_id.OPEN_MALARIA)
        self.assertEqual(model_id.parse("  oM"), model_id.OPEN_MALARIA)
        self.assertEqual(model_id.parse(model_id.OPEN_MALARIA), model_id.OPEN_MALARIA)
