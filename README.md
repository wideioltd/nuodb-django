# NuoDB - Django

[![Build Status](https://travis-ci.org/nuodb/nuodb-django.png?branch=master)](https://travis-ci.org/nuodb/nuodb-django)

This is the official Django adapter for [NuoDB](http://www.nuodb.com). It leverages the [NuoDB Python Driver](https://github.com/nuodb/nuodb-python).

### Requirements

If you haven't already, [Download and Install NuoDB](http://nuodb.com/download-nuodb/)

In the settings.py file in your project, set the `USE_TZ` flag to False. This is done because the timezone is detected when the connection is created. 

Set the `ENGINE` field in the `DATABASES/default` dictionary in settings.py to the django_pynuodb folder (if you installed using pip this is just `django_pynuodb`)

You can optionally set the schema by adding a `SCHEMA` field in the `DATABASES/default` dictionary in settings.py, if the schema is not specified it will default to `USER`

### Setup

git clone and install it 

```
git clone https://github.com/nuodb/nuodb-django.git
cd nuodb-django
python setup.py install
```

or install with pip

```
sudo pip install django_pynuodb
```

### Migrating from an existing Django app

To migrate data from an exiting Django app using a different database, the process is similar to migrating from another database to NuoDB using the [Migration Tool](http://doc.nuodb.com/display/doc/NuoDB+Migrator). The difference here is that we will be skpping the schema command. Django requires a specific file structure to function correctly, so in order to ensure that our Django app has the same structure in NuoDB as it does with a different database we will use Django's syncdb command to set up our schema.

To illustrate the steps involved we will use an app deployed with postgresql as an example...

Steps:

1) Using the NuoDB Migrator, dump the data from your postgresql Django app into a csv file.

```
$NUODB_HOME/bin/nuodb-migrator dump --source.driver=org.postgresql.Driver --source.url=jdbc:postgresql://localhost/test --source.username=postgres --output.type=csv --output.path=/tmp/dump.cat
```

2) From you Django app configured to use NuoDB (for an example of this look in the [Sample](#Sample) section below.) perform a syncdb.

```
python manage.py syncdb
```

3) We only performed this syncdb so that we could get the correct table structure for our database. The next step is to empty out the data that Django creates for us so that we have a clean database to import our data from postgresql. We do this using the TRUNCATE TABLE command in nuosql.

```
nuosql test --user dba --password goalie
SQL> show tables

	Tables in schema USER

		AUTH_GROUP
		AUTH_GROUP_PERMISSIONS
		AUTH_PERMISSION
		AUTH_USER
		AUTH_USER_GROUPS
		AUTH_USER_USER_PERMISSIONS
		DJANGO_CONTENT_TYPE
		DJANGO_SESSION
		DJANGO_SITE
SQL> truncate table user.auth_group;
SQL> truncate table user.auth_group_permissions;
SQL> truncate table user.auth_permission;
SQL> truncate table user.auth_user;
SQL> truncate table user.auth_user_groups;
SQL> truncate table user.auth_user_user_permissions;
SQL> truncate table user.django_content_type;
SQL> truncate table user.django_session;
SQL> truncate table user.django_site;
```

4) For our last step we need to import the data from our postgresql database into our new NuoDB database. For this we are going to use the NuoDB Migrator tool's load command.

```
$NUODB_HOME/bin/nuodb-migrator load --target.url=jdbc:com.nuodb://localhost/test?schema=USER --target.username=dba --target.password=goalie --input.path=/tmp/dump.cat
```


### Sample

Here is a sample database dictionary

```
DATABASES = {
    'default': {
        'ENGINE': 'django_pynuodb',
        'NAME': 'test',
        'DOMAIN_USER': 'domain',                        # domain credentials
        'DOMAIN_PASSWORD': 'bird',
        'DBA_USER': 'dba',	 			# database credentials
        'DBA_PASSWORD': 'goalie',
        'SCHEMA': '',  					# optional
        'HOST': 'localhost',
        'PORT': '48004',
    }
}
```

Set the `USE_TZ` flag to `False`

```
USE_TZ = False
```

### License

[NuoDB License](https://github.com/nuodb/nuodb-django/blob/master/LICENSE)
