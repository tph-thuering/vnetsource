"""
This is a library of useful commands created to help manage the VECNET CI datawarehouse.  Even though most of these
methods could be made more generic, they purposely haven't to control the data flow into and out of the DW.
"""
from struct import pack
import psycopg2

def encode_binary(pg_id, timestep, value, channel_key, run_key, replication_key):
    """ This method will encode a specific row of data into binary for fast ingestion.
    This is designed to encode data to a FactBaseTable row as of revision 753

    :param pg_id: Id for the new row in the database
    :type pg_id: Integer
    :returns: binary encoding of row, should be used with BytesIO to piece together with others
    :raises: TypeError
    """
    if not isinstance(pg_id, int):
        raise TypeError("id must be an integer, you passed in %(id)s which was a %(type)s" % {'id': pg_id, 'type': type(pg_id)})
    if not isinstance(timestep, int):
        raise TypeError("timestep must be an integer, you passed in %(ts)s which was a %(type)s" % {'ts': timestep, 'type': type(timestep)})
    if isinstance(value, int):
        # Convert to float
        value = float(value)
    elif not isinstance(value, float):
        raise TypeError("value must be a float, you passed in %(id)s which was a %(type)s" % {'id': value, 'type': type(value)})
    if not isinstance(channel_key, int):
        raise TypeError("channel_key must be an integer, you passed in %(id)s which was a %(type)s" % {'id': channel_key, 'type': type(channel_key)})
    if not isinstance(run_key, int):
        raise TypeError("run_key must be an integer, you passed in %(id)s which was a %(type)s" % {'id': run_key, 'type': type(run_key)})
    if not isinstance(replication_key, int):
        raise TypeError("replication_key must be an integer, you passed in %(id)s which was a %(type)s" % {'id': replication_key, 'type': type(replication_key)})
    # if not (timestep != -1 and value != -1.0 and channel_key != -1 and run_key != -1)
    ret_val = pack('!hiiiiidiiiiii', 6, 4, pg_id, 4, timestep, 8, value, 4, channel_key, 4, run_key, 4, replication_key)
    return ret_val

def commit_to_warehouse(pg_io, settings, table, pg_index):
    """
    This module will transmit a binary file that has been prepared to the database described in the setting dictionary
    and store it in the table described table.  To make this slightly more general, we do not assume a django settings
    dictionary is available.

    This will also set the id sequence to the proper value.

    :param pg_io: Bytes IO that contains the file (including headers) for the postgresql database
    :type pg_io: BytesIO
    :param settings: A dictionary that should contain keywords:
                     - HOST (ex vecnet.org)
                     - PORT (usually 5432)
                     - USER
                     - PASSWORD
                     - NAME (Name of the DB, for vecnet this is dw)
    :type settings: dict
    :param table: A string containing the table that the data should be appended to
    :type settings: str
    :param pg_index: Index to set the value of the id sequence to
    """
    pg_io.seek(0)
    conn = psycopg2.connect(
        host=settings['HOST'],
        port=settings['PORT'],
        user=settings['USER'],
        password=settings['PASSWORD'],
        database=settings['NAME']
    )
    data_cursor = conn.cursor()
    data_cursor.copy_expert('COPY %s FROM STDIN WITH BINARY' % table, pg_io)
    data_cursor.execute("select setval('base_fact_data_id_seq', %s);" % pg_index)
    data_cursor.close()
    conn.commit()
    conn.close()
    return

def frange(start, stop, step):
    """This is a generator for floating point ranges

    This will generate a series of values for a floating point stop, start, and step
    """
    i = start
    while i <= stop:
        yield i
        i += step