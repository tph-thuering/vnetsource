from abc import *
import keyword
import re

from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import connections, DEFAULT_DB_ALIAS


def table2model(table_name):
    """
    Turn the table_name into a model name.
    :param table_name: The name of the database table.
    :return: A string containing a model name.
    """
    return table_name.title().replace('_', '').replace(' ', '').replace('-', '')


class TableSelector:
    """
    Base class that represents how tables within the database are selected by the user.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def is_selected(self, table_name):
        raise NotImplementedError


class ListSelector(TableSelector):
    """
    A table selector based on a list of names.
    """

    def __init__(self, *names):
        """
        :param names: list of table names provided by the user
        """
        self.names = names

    def is_selected(self, table_name):
        return table_name in self.names


class PatternSelector(TableSelector):
    """
    A table selector based on a list of regular expressions.
    """
    def __init__(self, *patterns):
        """
        Initialize the selector with a list of regular expression patterns.
        """
        self.patterns = [re.compile(pattern) for pattern in patterns]

    def is_selected(self, table_name):
        for pattern in self.patterns:
            if pattern.search(table_name):
                return True
        return False


class Command(BaseCommand):
    """
    Custom copy of the built-in inspectdb command. Copied from bitbucket and modified.
    url: https://bitbucket.org/django/django/src/3b23a7a1691f/django/core/management/commands/inspectdb.py?at=default
    path:  django / django / core / management / commands / inspectdb.py
    """
    args = '<name | pattern> ...'
    help = "Introspects specific database tables in the given database and outputs a Django model module."

    option_list = BaseCommand.option_list + (
        make_option('--database', action='store', dest='database', default=DEFAULT_DB_ALIAS,
                    help='Nominates a database to introspect.  Defaults to using the "default" database.'),
        make_option('--regex', action='store_true', dest='regex', default=False,
                    help="Use the arguments as regular expressions to match table names."
                         "  Default: arguments are actual table names."),
        make_option('--list', action='store_true', dest='list_table_names', default=False,
                    help='List the existing tables in the database.'),
    )

    requires_model_validation = False

    db_module = 'django.db'

    def handle(self, *args, **options):
        try:
            for line in self.handle_inspection(options, *args):
                self.stdout.write("%s\n" % line)
        except NotImplementedError:
            raise CommandError("Database inspection isn't supported for the currently selected database backend.")

    def handle_inspection(self, options, *args):
        connection = connections[options.get('database')]

        cursor = connection.cursor()

        if options['list_table_names']:
            for table_name in connection.introspection.get_table_list(cursor):
                    yield table_name
            return

        yield "# This is an auto-generated Django model module."
        yield "# You'll have to do the following manually to clean this up:"
        yield "#     * Rearrange models' order"
        yield "#     * Make sure each model has one field with primary_key=True"
        yield "# Feel free to rename the models, but don't rename db_table values or field names."
        yield "#"
        yield "# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'"
        yield "# into your database."
        yield ''
        yield 'from %s import models' % self.db_module
        yield ''
        known_models = []
        if options['regex']:
            selector = PatternSelector(*args)
        else:
            selector = ListSelector(*args)

        for table_name in connection.introspection.get_table_list(cursor):
            if not selector.is_selected(table_name):
                continue
            yield 'class %s(models.Model):' % table2model(table_name)
            known_models.append(table2model(table_name))
            try:
                relations = connection.introspection.get_relations(cursor, table_name)
            except NotImplementedError:
                relations = {}
            try:
                indexes = connection.introspection.get_indexes(cursor, table_name)
            except NotImplementedError:
                indexes = {}
            for i, row in enumerate(connection.introspection.get_table_description(cursor, table_name)):
                column_name = row[0]
                att_name = column_name.lower()
                comment_notes = [] # Holds Field notes, to be displayed in a Python comment.
                extra_params = {}  # Holds Field parameters such as 'db_column'.

                # If the column name can't be used verbatim as a Python
                # attribute, set the "db_column" for this Field.
                if ' ' in att_name or '-' in att_name or keyword.iskeyword(att_name) or column_name != att_name:
                    extra_params['db_column'] = column_name

                # Add primary_key and unique, if necessary.
                if column_name in indexes:
                    if indexes[column_name]['primary_key']:
                        extra_params['primary_key'] = True
                    elif indexes[column_name]['unique']:
                        extra_params['unique'] = True

                # Modify the field name to make it Python-compatible.
                if ' ' in att_name:
                    att_name = att_name.replace(' ', '_')
                    comment_notes.append('Field renamed to remove spaces.')

                if '-' in att_name:
                    att_name = att_name.replace('-', '_')
                    comment_notes.append('Field renamed to remove dashes.')

                if column_name != att_name:
                    comment_notes.append('Field name made lowercase.')

                if i in relations:
                    rel_to = relations[i][1] == table_name and "'self'" or table2model(relations[i][1])

                    if rel_to in known_models:
                        field_type = 'ForeignKey(%s' % rel_to
                    else:
                        field_type = "ForeignKey('%s'" % rel_to

                    if att_name.endswith('_id'):
                        att_name = att_name[:-3]
                    else:
                        extra_params['db_column'] = column_name
                else:
                    # Calling `get_field_type` to get the field type string and any
                    # additional paramters and notes.
                    field_type, field_params, field_notes = self.get_field_type(connection, table_name, row)
                    extra_params.update(field_params)
                    comment_notes.extend(field_notes)

                    field_type += '('

                if keyword.iskeyword(att_name):
                    att_name += '_field'
                    comment_notes.append('Field renamed because it was a Python reserved word.')

                if att_name[0].isdigit():
                    att_name = 'number_%s' % att_name
                    extra_params['db_column'] = unicode(column_name)
                    comment_notes.append("Field renamed because it wasn't a "
                        "valid Python identifier.")

                # Don't output 'id = meta.AutoField(primary_key=True)', because
                # that's assumed if it doesn't exist.
                if att_name == 'id' and field_type == 'AutoField(' and extra_params == {'primary_key': True}:
                    continue

                # Add 'null' and 'blank', if the 'null_ok' flag was present in the
                # table description.
                if row[6]: # If it's NULL...
                    extra_params['blank'] = True
                    if not field_type in ('TextField(', 'CharField('):
                        extra_params['null'] = True

                field_desc = '%s = models.%s' % (att_name, field_type)
                if extra_params:
                    if not field_desc.endswith('('):
                        field_desc += ', '
                    field_desc += ', '.join(['%s=%r' % (k, v) for k, v in extra_params.items()])
                field_desc += ')'
                if comment_notes:
                    field_desc += ' # ' + ' '.join(comment_notes)
                yield '    %s' % field_desc
            for meta_line in self.get_meta(table_name):
                yield meta_line

    def get_field_type(self, connection, table_name, row):
        """
        Given the database connection, the table name, and the cursor row
        description, this routine will return the given field type name, as
        well as any additional keyword parameters and notes for the field.
        """
        field_params = {}
        field_notes = []

        try:
            field_type = connection.introspection.get_field_type(row[1], row)
        except KeyError:
            field_type = 'TextField'
            field_notes.append('This field type is a guess.')

        # This is a hook for DATA_TYPES_REVERSE to return a tuple of
        # (field_type, field_params_dict).
        if type(field_type) is tuple:
            field_type, new_params = field_type
            field_params.update(new_params)

        # Add max_length for all CharFields.
        if field_type == 'CharField' and row[3]:
            field_params['max_length'] = row[3]

        if field_type == 'DecimalField':
            field_params['max_digits'] = row[4]
            field_params['decimal_places'] = row[5]

        return field_type, field_params, field_notes

    def get_meta(self, table_name):
        """
        Return a sequence comprising the lines of code necessary
        to construct the inner Meta class for the model corresponding
        to the given database table name.
        """
        return ['    class Meta:',
                '        db_table = %r' % table_name,
                '']