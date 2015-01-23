"""
NuoDB database backend for Django.

Requires pynuodb: https://github.com/nuodb/nuodb-python
"""
import logging
import sys


from django.db.backends import *
from django.db import utils
from django.db.backends.signals import connection_created
from operations import DatabaseOperations
from client import DatabaseClient
from creation import DatabaseCreation
from version import get_version
from introspection import DatabaseIntrospection
from django.utils.encoding import force_str
from django.utils.safestring import SafeText, SafeBytes
from django.utils import six
from django.utils.timezone import utc


try:
    import pynuodb as Database
except ImportError as e:
    from django.core.exceptions import ImproperlyConfigured
    raise ImproperlyConfigured("Error loading pynuodb module: %s" % e)

from django_pynuodb.schema import DatabaseSchemaEditor

DatabaseError = Database.DatabaseError
IntegrityError = Database.IntegrityError

logger = logging.getLogger('django.db.backends')

def utc_tzinfo_factory(offset):
    if offset != 0:
        raise AssertionError("database connection isn't set to UTC")
    return utc

class CursorWrapper(object):
    """
    A thin wrapper around pynuodb's normal cursor class so that we can catch
    particular exception instances and re-raise them with the right types.
    """

    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, args=()):
        #print "CE"
        
        try:
            if type(query)==unicode:
                query=query.encode('utf8')
            args=map(lambda x:(x.encode('utf8') if type(x)==unicode else x),args)            
            query = str(query)
            #print query
            ## THIS WAS BUGGY BEFORE
            #if (query.startswith("ALTER")): # FIXME
            #  if not "ADD COLUMN" in queyry and "UNIQUE" in query:
            #    print "dropping query", query
            #    return None
            query = query % (("?",) * query.count("%s"))
            r= self.cursor.execute(query, args)
            #print "/CE"
            #print r
            return r            
        except Database.IntegrityError as e:
            six.reraise(utils.IntegrityError, utils.IntegrityError(*tuple(e.args)), sys.exc_info()[2])
        except Database.DatabaseError as e:
            #print e,utils
            #print e
            #print e.__dict__
            if not "duplicate" in e._Error__value:
              print e
              print "Q1",query, args
              six.reraise(utils.DatabaseError, utils.DatabaseError(*tuple(e.args)), sys.exc_info()[2])
            else:
              print "why duplicate ??"
              print "Q2",query,args
        except Database.OperationalError as e:
            #print e,utils            
            print query
            six.reraise(utils.DatabaseError, utils.DatabaseError(*tuple(e.args)), sys.exc_info()[2])

    def executemany(self, query, args):
        try:
            #print "EM"
            if type(query)==unicode:
                query=query.encode('utf8')
            args=map(lambda x:(x.encode('utf8') if type(x)==unicode else x),args)                        
            r=self.cursor.executemany(query, args)
            #print "/EM"
            return r
        except Database.IntegrityError as e:
            six.reraise(utils.IntegrityError, utils.IntegrityError(*tuple(e.args)), sys.exc_info()[2])
        except Database.DatabaseError as e:
            six.reraise(utils.DatabaseError, utils.DatabaseError(*tuple(e.args)), sys.exc_info()[2])
        except Database.OperationalError as e:
            #print e,utils
            six.reraise(utils.DatabaseError, utils.DatabaseError(*tuple(e.args)), sys.exc_info()[2])

    def __getattr__(self, attr):
        if attr in self.__dict__:
            return self.__dict__[attr]
        else:
            return getattr(self.cursor, attr)

    def __iter__(self):
        return iter(self.cursor)

class DatabaseFeatures(BaseDatabaseFeatures):
    allows_group_by_pk = True
    uses_savepoints = True
    allow_sliced_subqueries = False
    supports_select_related = False
    supports_unspecified_pk = True
    supports_forward_references = False
    supports_subqueries_in_group_by = False
    supports_bitwise_or = False
    supports_timezones = False
    needs_datetime_string_cast = False
    requires_rollback_on_dirty_transaction = True
    has_select_for_update = True
    supports_transactions = True
    can_introspect_foreign_keys = False
    related_fields_match_type=True
    
    #empty_fetchmany_value = ()
    #update_can_self_select = False
    #allows_group_by_pk = True
    #related_fields_match_type = True
    ##allow_sliced_subqueries = False
    ##has_bulk_insert = True
    #has_select_for_update = True
    #has_select_for_update_nowait = False
    #supports_forward_references = False
    #supports_long_model_names = False
    ## XXX MySQL DB-API drivers currently fail on binary data on Python 3.
    #supports_binary_field = six.PY2
    #supports_microsecond_precision = False
    #supports_regex_backreferencing = False
    #supports_date_lookup_using_string = False
    #can_introspect_binary_field = False
    #can_introspect_boolean_field = False
    ##supports_timezones = False
    ##requires_explicit_null_ordering_when_grouping = True
    #allows_auto_pk_0 = False
    ##uses_savepoints = True
    atomic_transactions = True
    #supports_column_check_constraints = False
    
    
#parse_datetime = conversions[FIELD_TYPE.DATETIME]


#def parse_datetime_with_timezone_support(value):
    #dt = parse_datetime(value)
    ## Confirm that dt is naive before overwriting its tzinfo.
    #if dt is not None and settings.USE_TZ and timezone.is_naive(dt):
        #dt = dt.replace(tzinfo=timezone.utc)
    #return dt


#def adapt_datetime_with_timezone_support(value, conv):
    ## Equivalent to DateTimeField.get_db_prep_value. Used only by raw SQL.
    #if settings.USE_TZ:
        #if timezone.is_naive(value):
            #warnings.warn("MySQL received a naive datetime (%s)"
                          #" while time zone support is active." % value,
                          #RuntimeWarning)
            #default_timezone = timezone.get_default_timezone()
            #value = timezone.make_aware(value, default_timezone)
        #value = value.astimezone(timezone.utc).replace(tzinfo=None)
    #return Thing2Literal(value.strftime("%Y-%m-%d %H:%M:%S"), conv)


#django_conversions = conversions.copy()
#django_conversions.update({
    #FIELD_TYPE.TIME: backend_utils.typecast_time,
    #FIELD_TYPE.DECIMAL: backend_utils.typecast_decimal,
    #FIELD_TYPE.NEWDECIMAL: backend_utils.typecast_decimal,
    #FIELD_TYPE.DATETIME: parse_datetime_with_timezone_support,
    #datetime.datetime: adapt_datetime_with_timezone_support,
#})


class DatabaseWrapper(BaseDatabaseWrapper):
    vendor = 'nuodb'
    operators = {
        'exact': '= %s',
        'iexact': '= UPPER(%s)',
        'contains': 'LIKE %s',
        'icontains': 'LIKE UPPER(%s)',
        'regex': '~ %s',
        'iregex': '~* %s',
        'gt': '> %s',
        'gte': '>= %s',
        'lt': '< %s',
        'lte': '<= %s',
        'startswith': 'LIKE %s',
        'endswith': 'LIKE %s',
        'istartswith': 'LIKE UPPER(%s)',
        'iendswith': 'LIKE UPPER(%s)',
    }
    
    Database = Database

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, **kwargs)

        self.features = DatabaseFeatures(self)
        autocommit = self.settings_dict["OPTIONS"].get('autocommit', False)
        self.features.uses_autocommit = autocommit        
        self.ops = DatabaseOperations(self)
        self.client = DatabaseClient(self)
        self.creation = DatabaseCreation(self)
        self.introspection = DatabaseIntrospection(self)
        self.validation = BaseDatabaseValidation(self)
        self._nuodb_version = None


    def get_connection_params(self):
        if not self.settings_dict['NAME']:
                from django.core.exceptions import ImproperlyConfigured
                raise ImproperlyConfigured(
                    "settings.DATABASES is improperly configured. "
                    "Please supply the NAME value.")
        settings_dict=self.settings_dict
        conn_params = {
            'database': settings_dict['NAME'],
        }
        conn_params.update(settings_dict['OPTIONS'])
        #if 'autocommit' in conn_params:
        #    del conn_params['autocommit']
        
        if settings_dict.has_key('SCHEMA'):
            options = {"schema": settings_dict.get('SCHEMA', 'user') or 'user'}
        else:
            options = {"schema": "user"}
        
        if settings_dict['DBA_USER']:
            conn_params['user'] = settings_dict['DBA_USER']
        if settings_dict['DBA_PASSWORD']:
            conn_params['password'] = force_str(settings_dict['DBA_PASSWORD'])
        if settings_dict['HOST']:
            conn_params['host'] = settings_dict['HOST']
        if settings_dict['PORT']:
            options['port'] = settings_dict['PORT']
        tz = 'UTC' if settings.USE_TZ else settings_dict.get('TIME_ZONE')
#             options['timezone'] = tz
        conn_params['options'] = options
        return conn_params


    def close(self):
        if self.connection is None:
            return

        try:
            self.connection.close()
            self.connection = None
        except Database.Error:
            # In some cases (database restart, network connection lost etc...)
            # the connection to the database is lost without giving Django a
            # notification. If we don't set self.connection to None, the error
            # will occur a every request.
            self.connection = None
            logger.warning('pynuodb error while closing the connection.',
                exc_info=sys.exc_info()
            )
            raise

    def _get_nuodb_version(self):
        if self._nuodb_version is None:
            self._nuodb_version = get_version(self.connection)
        return self._nuodb_version
    
    nuodb_version = property(_get_nuodb_version)

    def get_new_connection(self,conn_params):
       conn = Database.connect(**conn_params)
       autocommit=conn_params.get('autocommit', self.settings_dict["OPTIONS"].get('autocommit', True))       
       c=conn.cursor()
       c.execute("SET AUTOCOMMIT "+("ON" if autocommit else "OFF")+";")
       c.close()
       return conn
     
    def create_cursor(self):
        cursor = self.connection.cursor()
        cursor.tzinfo_factory = utc_tzinfo_factory if settings.USE_TZ else None
        return CursorWrapper(cursor)
     
    #def _cursor(self):
        #settings_dict = self.settings_dict
        #if self.connection is None:
            #if not settings_dict['NAME']:
                #from django.core.exceptions import ImproperlyConfigured
                #raise ImproperlyConfigured(
                    #"settings.DATABASES is improperly configured. "
                    #"Please supply the NAME value.")
            #conn_params = {
                #'database': settings_dict['NAME'],
            #}
            #conn_params.update(settings_dict['OPTIONS'])
            #if 'autocommit' in conn_params:
                #del conn_params['autocommit']
            
            #if settings_dict.has_key('SCHEMA'):
                #options = {"schema": settings_dict.get('SCHEMA', 'user') or 'user'}
            #else:
                #options = {"schema": "user"}
            
            #if settings_dict['DBA_USER']:
                #conn_params['user'] = settings_dict['DBA_USER']
            #if settings_dict['DBA_PASSWORD']:
                #conn_params['password'] = force_str(settings_dict['DBA_PASSWORD'])
            #if settings_dict['HOST']:
                #conn_params['host'] = settings_dict['HOST']
            #if settings_dict['PORT']:
                #options['port'] = settings_dict['PORT']
            #tz = 'UTC' if settings.USE_TZ else settings_dict.get('TIME_ZONE')
##             options['timezone'] = tz
            #conn_params['options'] = options
            #self.connection = Database.connect(**conn_params)
            #if tz:
                #try:
                    #get_parameter_status = self.connection.get_parameter_status
                #except AttributeError:
                    #conn_tz = None
                #else:
                    #conn_tz = get_parameter_status('TimeZone')
            #self._get_nuodb_version()
            #connection_created.send(sender=self.__class__, connection=self)
        #cursor = self.connection.cursor()
        #cursor.tzinfo_factory = utc_tzinfo_factory if settings.USE_TZ else None
        #return CursorWrapper(cursor)

    def _set_autocommit(self, autocommit):
            c=self.connection.cursor()
            c.execute("SET AUTOCOMMIT "+("ON" if autocommit else "OFF")+";")
            c.close()

    def init_connection_state(self):
        tz = 'UTC' if settings.USE_TZ else self.settings_dict.get('TIME_ZONE')
        if tz:
            try:
                get_parameter_status = self.connection.get_parameter_status
            except AttributeError:
                conn_tz = None
            else:
                conn_tz = get_parameter_status('TimeZone')
        self._get_nuodb_version()
        connection_created.send(sender=self.__class__, connection=self)      
        with self.cursor() as cursor:
          pass

    def _set_isolation_level(self, level):
        """
        Do all the related feature configurations for changing isolation
        levels. This doesn't touch the uses_autocommit feature, since that
        controls the movement *between* isolation levels.
        """
        assert level in range(5)
        try:
            if self.connection is not None:
                pass
#                 self.connection.set_isolation_level(level)
        finally:
            self.isolation_level = level
            self.features.uses_savepoints = bool(level)

    def _commit(self):
        if self.connection is not None:
            try:
                return self.connection.commit()
            except Database.IntegrityError as e:
                six.reraise(utils.IntegrityError, utils.IntegrityError(*tuple(e.args)), sys.exc_info()[2])
    def schema_editor(self, *args, **kwargs):
        "Returns a new instance of this backend's SchemaEditor"
        return DatabaseSchemaEditor(self, *args, **kwargs)
