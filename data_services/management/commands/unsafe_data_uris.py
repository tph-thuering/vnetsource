from copy import copy
import hashlib
from optparse import make_option, Option, OptionValueError

from django.core.management.base import BaseCommand, CommandError

from ...sim_file_server.uri_schemes.data_scheme import DataSchemeHandler
from ...models import SimulationInputFile, SimulationOutputFile


def check_print_length(option, opt, value):
    """
    Check the value given to the --print-length option.
    """
    if value == "all":
        return value
    try:
        value = int(value)
    except ValueError:
        raise OptionValueError("option %s: invalid integer: %r" % (opt, value))
    if value < 1:
        raise OptionValueError('option %s: integer must be = or > 1' % opt)
    return value


class PrintLengthOption(Option):
    TYPES = Option.TYPES + ("PrintLength",)
    TYPE_CHECKER = copy(Option.TYPE_CHECKER)
    TYPE_CHECKER["PrintLength"] = check_print_length
    DEFAULT = 60


class Command(BaseCommand):
    args = '[FILE_TYPE]'
    help = '''Find any "data" scheme URIs for simulation files that are unsafe

Arguments:
  FILE_TYPE  The type of data files to search:
               input  = just simulation input files
               output = just simulation output files
             (default : both input and output)'''

    option_list = BaseCommand.option_list + (
        make_option('--verify-checksum',
                    action='store_true',
                    dest='verify_checksum',
                    default=False,
                    help='Verify the MD5 checksum on the unsafe URIs'),
        make_option('--fix-checksum',
                    action='store_true',
                    dest='fix_checksum',
                    default=False,
                    help='Fix missing or invalid MD5 checksum on the unsafe URIs'),
        make_option('--fix-uri',
                    action='store_true',
                    dest='fix_uri',
                    default=False,
                    help='Fix unsafe URIs.  Checksums are also fixed.'),
        PrintLengthOption('--print-length',
                          type='PrintLength',
                          action='store',
                          dest='print_length',
                          default=PrintLengthOption.DEFAULT,
                          metavar='INTEGER|all',
                          help='Maximum # of characters to print for each URI (default: {}).'.
                               format(PrintLengthOption.DEFAULT) +
                               '  Use "all" to print all characters (warning: some all very long).'),
        )

    def handle(self, *args, **options):
        db_models_to_search = process_arguments(*args)
        verify_checksum = options['verify_checksum']
        fix_checksum = options['fix_checksum']
        fix_uri = options['fix_uri']
        if fix_uri:
            # Doesn't make sense to fix URIs without fixing their checksums too
            fix_checksum = True
        if fix_checksum:
            # Fixing them requires first verifying them
            verify_checksum = True
        uri_formatter = Formatter(options['print_length'])

        data_scheme_handler = DataSchemeHandler()

        for database_model in db_models_to_search:
            data_files = database_model.objects.all()
            self.stdout.write('Scanning {:,} data files in the {} table...'.format(data_files.count(),
                                                                                   database_model.__name__))
            UNSAFE_URI_PREFIX = 'data:,'
            unsafe_uris = database_model.objects.filter(uri__startswith=UNSAFE_URI_PREFIX)
            self.stdout.write('{:,} files have unsafe URIs'.format(unsafe_uris.count()))

            for data_file in unsafe_uris:
                self.stdout.write(' {:,} : {}'.format(data_file.id, uri_formatter(data_file.uri)))
                if verify_checksum or fix_checksum:
                    checksum_needs_fixed = False
                    data = data_file.uri[len(UNSAFE_URI_PREFIX):]
                    try:
                        stored_md5 = data_file.metadata[SimulationInputFile.MetadataKeys.CHECKSUM]
                        computed_md5 = hashlib.md5(data).hexdigest()
                        if stored_md5 != computed_md5:
                            self.stdout.write('   Stored MD5 checksum does not match computed MD5 checksum')
                            self.stdout.write('     stored   = {}'.format(stored_md5))
                            self.stdout.write('     computed = {}'.format(computed_md5))
                            checksum_needs_fixed = True
                    except KeyError:
                        self.stdout.write('   Missing MD5 checksum')
                        computed_md5 = None
                        checksum_needs_fixed = True
                    if fix_checksum and checksum_needs_fixed:
                        if computed_md5 is None:
                            computed_md5 = hashlib.md5(data).hexdigest()
                        data_file.metadata[SimulationInputFile.MetadataKeys.CHECKSUM] = computed_md5
                        data_file.metadata[SimulationInputFile.MetadataKeys.CHECKSUM_ALGORITHM] = \
                            SimulationInputFile.ChecksumAlgorithms.MD5
                        data_file.save()
                        self.stdout.write('   Set MD5 checksum to {}'.format(computed_md5))

                if fix_uri:
                    safe_uri, new_md5 = data_scheme_handler.store_file(data)
                    if new_md5 != computed_md5:
                        self.stdout.write('   MD5 checksum for new safe URI does not match computed MD5 checksum')
                        self.stdout.write('     new      = {}'.format(new_md5))
                        self.stdout.write('     computed = {}'.format(computed_md5))
                    else:
                        data_file.uri = safe_uri
                        data_file.save()
                        self.stdout.write('   Fixed uri {}'.format(uri_formatter(safe_uri)))


class Formatter(object):
    """
    Formats URIs for display by truncating them to a specific length and delimiting them with double quotes (").
    """

    def __init__(self, print_length):
        self.print_length = print_length
        if print_length == 'all':
            self.truncate = lambda text: text
        else:
            self.truncate = lambda text: text[0:self.print_length]

    def __call__(self, text):
        truncated_text = self.truncate(text)
        formatted_text = '"{}"'.format(truncated_text)
        if len(truncated_text) < len(text):
            formatted_text += '...'
        return formatted_text


def process_arguments(*args):
    """
    Process the positional arguments from the command line.

    :param sequence args: The arguments
    :return: A tuple of database models that should be searched.  Each data model represents a type of simulation
             data file.
    """
    if len(args) == 0:
        # Default
        return SimulationInputFile, SimulationOutputFile
    if len(args) > 1:
        raise CommandError('Additional arguments after FILE_TYPE: ' + ' '.join(args[1:]))
    if args[0] == 'input':
        return SimulationInputFile,
    elif args[0] == 'output':
        return SimulationOutputFile,
    else:
        raise CommandError('Unknown FILE_TYPE: ' + args[0])
