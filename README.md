# NuoDB - Django

[![Build Status](https://travis-ci.org/nuodb/nuodb-django.png?branch=master)](https://travis-ci.org/nuodb/nuodb-django)

This is the official Django adapter for [NuoDB](http://www.nuodb.com). It leverages the [NuoDB Python Driver](https://github.com/nuodb/nuodb-python).

### Requirements

If you haven't already, [Download and Install NuoDB](http://nuodb.com/download-nuodb/)

In the settings.py file in your project, set the `USE_TZ` flag to False. This is done because the timezone is detected when the connection is created. 

Set the `ENGINE` field in the `DATABASES/default` dictionary in settings.py to the django_pynuodb folder (if you installed using pip this is just `django_pynuodb`)

You can optionally set the schema by adding a `SCHEMA` field in the `DATABASES/default` dictionary in settings.py, if the schema is not specified it will default to `USER`

### Setup

1 - git clone https://github.com/nuodb/nuodb-django.git

or install with pip

2 - pip install django_pynuodb


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

[NuoDB License](https://github.com/nuodb/nuodb-drivers/blob/master/LICENSE)
