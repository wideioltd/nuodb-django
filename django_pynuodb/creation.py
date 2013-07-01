# import psycopg2.extensions
import pynuodb.entity
import tempfile
import unittest
import time
import os
import string
import random
import sys

from django.db.backends.creation import BaseDatabaseCreation
from django.db.backends.util import truncate_name

HOST            = "localhost"
DOMAIN_USER     = "domain"
DOMAIN_PASSWORD = "bird"

DBA_USER        = 'dba'
DBA_PASSWORD    = 'dba_password'
DATABASE_NAME   = 'test_test'

class DatabaseCreation(BaseDatabaseCreation):
    # This dictionary maps Field objects to their associated PostgreSQL column
    # types, as strings. Column-type strings can contain format strings; they'll
    # be interpolated against the values of Field.__dict__ before being output.
    # If a column type is set to None, it won't be included in the output.
    data_types = {
        'AutoField':         'serial',
        'BooleanField':      'boolean',
        'CharField':         'varchar(%(max_length)s)',
        'CommaSeparatedIntegerField': 'varchar(%(max_length)s)',
        'DateField':         'date',
        'DateTimeField':     'timestamp with time zone',
        'DecimalField':      'numeric(%(max_digits)s, %(decimal_places)s)',
        'FileField':         'varchar(%(max_length)s)',
        'FilePathField':     'varchar(%(max_length)s)',
        'FloatField':        'double precision',
        'IntegerField':      'integer',
        'BigIntegerField':   'bigint',
        'IPAddressField':    'inet',
        'GenericIPAddressField': 'inet',
        'NullBooleanField':  'boolean',
        'OneToOneField':     'integer',
        'PositiveIntegerField': 'integer CHECK ("%(column)s" >= 0)',
        'PositiveSmallIntegerField': 'smallint CHECK ("%(column)s" >= 0)',
        'SlugField':         'varchar(%(max_length)s)',
        'SmallIntegerField': 'smallint',
        'TextField':         'text',
        'TimeField':         'time',
    }

    def sql_table_creation_suffix(self):
        assert self.connection.settings_dict['TEST_COLLATION'] is None, "NuoDB does not support collation setting at database creation time."
        if self.connection.settings_dict['TEST_CHARSET']:
            return "WITH ENCODING '%s'" % self.connection.settings_dict['TEST_CHARSET']
        return ''

    def sql_indexes_for_field(self, model, f, style):
        output = []
        if f.db_index or f.unique:
            qn = self.connection.ops.quote_name
            db_table = model._meta.db_table
            tablespace = f.db_tablespace or model._meta.db_tablespace
            if tablespace:
                tablespace_sql = self.connection.ops.tablespace_sql(tablespace)
                if tablespace_sql:
                    tablespace_sql = ' ' + tablespace_sql
            else:
                tablespace_sql = ''

            def get_index_sql(index_name, opclass=''):
                return (style.SQL_KEYWORD('CREATE INDEX') + ' ' +
                        style.SQL_TABLE(qn(truncate_name(index_name,self.connection.ops.max_name_length()))) + ' ' +
                        style.SQL_KEYWORD('ON') + ' ' +
                        style.SQL_TABLE(qn(db_table)) + ' ' +
                        "(%s%s)" % (style.SQL_FIELD(qn(f.column)), opclass) +
                        "%s;" % tablespace_sql)

            if not f.unique:
                output = [get_index_sql('%s_%s' % (db_table, f.column))]

            # Fields with database column types of `varchar` and `text` need
            # a second index that specifies their operator class, which is
            # needed when performing correct LIKE queries outside the
            # C locale. See #12234.
            db_type = f.db_type(connection=self.connection)
            if db_type.startswith('varchar'):
                output.append(get_index_sql('%s_%s_like' % (db_table, f.column),
                                            ' varchar_pattern_ops'))
            elif db_type.startswith('text'):
                output.append(get_index_sql('%s_%s_like' % (db_table, f.column),
                                            ' text_pattern_ops'))
        return output

    def set_autocommit(self):
        self._prepare_for_test_db_ddl()


    def _create_test_db(self, verbosity, autoclobber):
        """
        Internal implementation - creates the test db tables.
        """
        domain = pynuodb.entity.Domain(HOST, DOMAIN_USER, DOMAIN_PASSWORD)
        try:
            test_database_name = self._get_test_db_name()
            if test_database_name not in [db.getName() for db in domain.getDatabases()]:
                peer = domain.getEntryPeer()
                archive = os.path.join(tempfile.gettempdir(), ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(20)))
                peer.startStorageManager(test_database_name, archive, True, waitSeconds=10)
                peer.startTransactionEngine(test_database_name,  [('--dba-user', DBA_USER),('--dba-password', DBA_PASSWORD)], waitSeconds=10)
            return test_database_name
        finally:
            domain.disconnect()
            

    def destroy_test_db(self, old_database_name, verbosity=1):
        """
        Destroy a test database, prompting the user for confirmation if the
        database already exists.
        """
        self.connection.close()
        test_database_name = self.connection.settings_dict['NAME']
        if verbosity >= 1:
            test_db_repr = ''
            if verbosity >= 2:
                test_db_repr = " ('%s')" % test_database_name
            print("Destroying test database for alias '%s'%s..." % (
                self.connection.alias, test_db_repr))

        # Temporarily use a new connection and a copy of the settings dict.
        # This prevents the production database from being exposed to potential
        # child threads while (or after) the test database is destroyed.
        # Refs #10868 and #17786.
        settings_dict = self.connection.settings_dict.copy()
        settings_dict['NAME'] = old_database_name
        backend = load_backend(settings_dict['ENGINE'])
        new_connection = backend.DatabaseWrapper(
                             settings_dict,
                             alias='__destroy_test_db__',
                             allow_thread_sharing=False)
        new_connection.creation._destroy_test_db(test_database_name, verbosity)

    def _destroy_test_db(self, test_database_name, verbosity):
        """
        Internal implementation - remove the test db tables.
        """
        listener = TestDomainListener()
        domain = pynuodb.entity.Domain(HOST, DOMAIN_USER, DOMAIN_PASSWORD, listener)
        try:
            database = domain.getDatabase(test_database_name)
            if database is not None:
                for process in database.getProcesses():
                    process.shutdown()
                    
                for i in xrange(1,20):
                    time.sleep(0.25)
                    if listener.db_left:
                        time.sleep(1)
                        break
        finally:
            domain.disconnect()

    def _prepare_for_test_db_ddl(self):
        """Rollback and close the active transaction."""
        self.connection.connection.rollback()
#         self.connection.connection.set_isolation_level(
#                 psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
