import os
import re
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    args = '<app | path>'
    help = 'Output a models module in canonical form for comparison'

    option_list = BaseCommand.option_list + (
        make_option('--file',
                    action='store_false',
                    dest='is_app',
                    default=True,
                    help='The argument is a path to a models module file'),
        )

    def handle(self, *args, **options):
        is_app = options['is_app']
        if is_app:
            arg_desc = 'app name'
        else:
            arg_desc = 'file path'

        if len(args) == 0:
            raise CommandError('Missing %s' % arg_desc)
        if len(args) > 1:
            raise CommandError('More than one %s specified' % arg_desc)
        if is_app:
            app = args[0]
            models_module_file = app + '/models.py'
        else:
            models_module_file = args[0]

        if not os.path.exists(models_module_file):
            raise CommandError('The file "%s" does not exist' % models_module_file)
        try:
            with open(models_module_file, 'r') as f:
                models_code = [line.rstrip() for line in f]
        except IOError, exc:
            raise CommandError('Cannot read the file "%s" (%s)' % (models_module_file, str(exc)))

        canonical_code = make_canonical_form(models_code)
        for line in canonical_code:
            self.stdout.write(line)


def make_canonical_form(models_code):
    """Convert the source code for data models into a canonical form.

    The canonical form is:
      *  comment lines removed
      *  model classes are in alphabetical order
      *  all blank lines removed except one blank line before each model class
    """
    #  Remove blank lines
    models_code = [line for line in models_code if not is_blank(line)]

    #  Remove comment lines
    models_code = [line for line in models_code if not is_comment(line)]

    #  Remove these lines because inspectdb doesn't output them:
    #      app_label = 'datawarehouse'
    models_code = [line for line in models_code if not is_app_label(line)]

    #  Remove the primary keys that inspectdb outputs since they aren't in models.py (usually)
    models_code = [line for line in models_code if not is_id_field(line)]

    #  Change the unicode literals in the inspectdb output to string literals
    #  For example, change this line:
    #
    #       db_table = u'dim_foo_bar'
    #
    #  to this:
    #
    #       db_table = 'dim_foo_bar'
    models_code = [line.replace("db_table = u'", "db_table = '") for line in models_code if not is_id_field(line)]

    #  Group lines for each class definition
    lines_before_first_class = []
    current_class_def = lines_before_first_class
    class_code = dict()
    class_pattern = re.compile(r'class\s+(?P<name>\w+)\(models.Model\)\:')
    for line in models_code:
        class_line = class_pattern.match(line)
        if class_line:
            #  Start a new list for the class' source lines
            class_name = class_line.group('name')
            current_class_def = [line]
            class_code[class_name] = current_class_def
        else:
            #  Add the current line to the current class definition
            current_class_def.append(line)

    class_names = class_code.keys()
    class_names.sort()

    canonical_form = list(lines_before_first_class)
    for name in class_names:
        canonical_form.append('')  #  Blank line before model class
        canonical_form.extend(class_code[name])
    return canonical_form


def is_blank(line):
    """Is a line from a file blank (i.e., empty or just whitespace)?
    """
    return re.match(r'^\s*$', line)


def is_comment(line):
    """Is a line a Python comment line (i.e., first non-whitespace character is "#")?
    """
    return re.match(r'^\s*#', line)


def is_app_label(line):
    """Does the line have an app_label statement?
    """
    return re.match(r'^\s*app_label\s+=', line)


def is_id_field(line):
    """Does the line define the primary key "id" field?
    """
    return line == "    id = models.IntegerField(primary_key=True)"
