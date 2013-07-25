sudo apt-get install python-pip
sudo pip install Django
sudo pip install pynuodb
sudo pip install django_pynuodb
#sudo apt-get install python-django

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

cd /tmp
git clone https://github.com/nuodb/nuodb-django.git

#cd /opt/nuodb
#./run-quickstart

cd /tmp/nuodb_site
yes | python manage.py syncdb

#python manage.py test

