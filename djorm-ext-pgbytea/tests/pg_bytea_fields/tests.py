# -*- coding: utf-8 -*-

from django.test import TestCase
from djorm_pgbytea.fields import ByteaField, LargeObjectFile

from .models import ByteaModel, LargeObjectModel

import hashlib
import os.path
import io


class BinaryDataTest(TestCase):
    def setUp(self):
        ByteaModel.objects.all().delete()
        LargeObjectModel.objects.all().delete()

    def test_internals_bytea_field(self):
        field = ByteaField()
        prep_value = field.get_db_prep_value(None, connection=None)
        self.assertEqual(prep_value, None)

    def test_simple_insert_on_bytea_field(self):
        path = os.path.join(os.path.dirname(__file__), "test.jpg")
        data = ''

        with io.open(path, "rb") as f:
            data = f.read()

        strhash = hashlib.sha256(data).hexdigest()
        obj = ByteaModel.objects.create(data=data)
        obj = ByteaModel.objects.get(pk=obj.id)

        self.assertEqual(strhash, hashlib.sha256(obj.data).hexdigest())

    def test_insert_void_to_bytea_field(self):
        obj = ByteaModel.objects.create(data=None)
        obj = ByteaModel.objects.get(pk=obj.id)
        self.assertEqual(obj.data, None)

    def test_isnull_search_on_bytea_field(self):
        obj1 = ByteaModel.objects.create(data=None)
        obj2 = ByteaModel.objects.create(data='ABCD')
        obj3 = ByteaModel.objects.create(data=None)

        null_objs = ByteaModel.objects.filter(data__isnull=True)
        self.assertEqual(null_objs.count(), 2)
        self.assertEqual(set(null_objs), set([obj1, obj3]))

        non_null_objs = ByteaModel.objects.filter(data__isnull=False)
        self.assertEqual(non_null_objs.count(), 1)
        self.assertEqual(set(non_null_objs), set([obj2]))

        # Confirm that data=None is an alias for __isnull.
        self.assertEqual(set(null_objs),
                          set(ByteaModel.objects.filter(data=None)))
        self.assertEqual(set(non_null_objs),
                          set(ByteaModel.objects.exclude(data=None)))

    def test_other_search_on_bytea_field(self):
        ByteaModel.objects.create(data=None)
        ByteaModel.objects.create(data='ABCD')
        self.assertRaises(TypeError, ByteaModel.objects.filter, data='ABCD')

    def test_create_void_large_object(self):
        LargeObjectModel.objects.create(lobj=None)

    def test_create_invalid_large_object(self):
        with self.assertRaises(ValueError):
            LargeObjectModel.objects.create(lobj=LargeObjectFile())

    def test_write_simple_large_object(self):
        lobj = LargeObjectFile()
        lobj.open()

        path = os.path.join(os.path.dirname(__file__), "test.jpg")

        with io.open(path, "rb") as f:
            lobj.write(f.read())
            lobj.close()

        instance = LargeObjectModel.objects.create(lobj=lobj)
        instance = LargeObjectModel.objects.get(pk=instance.pk)

        with io.open(path, "rb") as f:
            original_data = f.read()

            instance.lobj.open()
            database_data = instance.lobj.read()

            self.assertEqual(original_data, database_data)
