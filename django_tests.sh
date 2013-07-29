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

#Changing the manage path
cd /tmp/nuodb_site
sed -i "s#/usr/bin/env python#/home/travis/virtualenv/python2.7/bin/env python#" manage.py

export PYTHONPATH=/home/travis/virtualenv/python2.7/lib/python2.7/site-packages/django/

cd /tmp/nuodb_site
yes | python manage.py syncdb

cd /home/travis/virtualenv/python2.7/lib/python2.7/site-packages/django && localhost
cd /home/travis/virtualenv/python2.7/lib/python2.7/dist-packages/django && localhost

#Skipping unsupported tests
sudo chmod 777 /home/travis/virtualenv/python2.7/lib/python2.7/site-packages/django/contrib/sessions/tests.py
sed -i '1s/^/from django.test.testcases import skipIfDBFeature\n/' /usr/local/lib/python2.7/lib/python2.7/site-packages/django/contrib/sessions/tests.py
sed -i "s/@override_settings(USE_TZ=True)/#@override_settings(USE_TZ=True)/" /home/travis/virtualenv/python2.7/lib/python2.7/site-packages/django/contrib/sessions/tests.py
sed -i "s/@override_settings(USE_TZ=True)/#@override_settings(USE_TZ=True)/" /home/travis/virtualenv/python2.7/lib/python2.7/site-packages/django/contrib/sessions/tests.py

# sudo chmod 777 /usr/local/lib/python2.7/dist-packages/django/contrib/sites/tests.py
# sed -i '1s/^/from django.test.testcases import skipIfDBFeature\n/' /usr/local/lib/python2.7/dist-packages/django/contrib/sites/tests.py
# sed -i "s/class SitesFrameworkTests(TestCase):/class SitesFrameworkTests(TestCase):\n    @skipIfDBFeature('supports_transactions')/" /usr/local/lib/python2.7/dist-packages/django/contrib/sites/tests.py

# sudo chmod 777 /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/context_processors.py
# sed -i '1s/^/from django.test.testcases import skipIfDBFeature\n/' /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/context_processors.py
# sed -i "s/def test_perms_attrs(self):/@skipIfDBFeature('supports_transactions')\n    def test_perms_attrs(self):/" /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/context_processors.py
# sed -i "s/def test_perms_attrs(self):/@skipIfDBFeature('supports_transactions')\n    def test_perm_in_perms_attrs(self):/" /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/context_processors.py

# sudo chmod 777 /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/remote_user.py
# sed -i '1s/^/from django.test.testcases import skipIfDBFeature\n/' /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/remote_user.py
# sed -i "s/def test_last_login(self):/@skipIfDBFeature('supports_transactions')\n    def test_last_login(self):/" /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/remote_user.py

# sudo chmod 777 /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/tokens.py
# sed -i '1s/^/from django.test.testcases import skipIfDBFeature\n/' /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/tokens.py
# sed -i "s/def test_10265(self):/@skipIfDBFeature('supports_transactions')\n    def test_10265(self):/" /usr/local/lib/python2.7/dist-packages/django/contrib/auth/tests/tokens.py