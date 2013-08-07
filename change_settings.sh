cd /tmp
django-admin.py startproject nuodb_site
cd /tmp/nuodb_site/nuodb_site
sed -i "s/'ENGINE': 'django.db.backends.',/'ENGINE': 'django_pynuodb', 'NAME':'test',/" settings.py
sed -i "s/'NAME': '',/'USER': 'dba',/" settings.py
sed -i "s/'USER': '',/'SCHEMA': 'django',/" settings.py
sed -i "s/'PASSWORD': '',/'PASSWORD': 'goalie',/" settings.py
sed -i "s/'HOST': '',/'HOST': 'localhost',/" settings.py
sed -i "s/'PORT': '',/'PORT': '48004',/" settings.py
sed -i "s/USE_TZ = True/USE_TZ = False/" settings.py
