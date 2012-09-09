# Deploy script, to deploy to webfaction currently
import os
from datetime import datetime

from fabric.api import *

env.user = 'f4nt'
env.hosts = ['gmecol.f4ntasmic.com']

PROJECT_ROOT = '/home/f4nt/webapps/gmecol_django'


def run_tests():
    with lcd('collector'):
        local('python manage.py test gmecol')


def restart_apache():
    run(os.path.join(PROJECT_ROOT, 'apache2/bin/restart'))


def restart_memcached():
    with settings(warn_only=True):
        # If it fails, then this instance must have died
        run('kill `cat /home/f4nt/memcached.pid`')
    run('memcached -d -m 64 -s /home/f4nt/memcached.sock -P '
        '/home/f4nt/memcached.pid')


def create_build():
    with cd(os.path.join(PROJECT_ROOT, 'builds')):
        run('mv gmecol_project gmecol_project_%s' % datetime.now().strftime(
            '%Y-%m-%d-%H_%M_%S'
            ))
        run('git clone git://github.com/f4nt/gmecol_project.git gmecol_project')


def deploy_build():
    with prefix(('export PYTHONPATH=/home/f4nt/webapps/gmecol_django:'
            '/home/f4nt/webapps/gmecol_django/gmecol_project/'
            'collector:/home/f4nt/webapps/gmecol_django/lib/python2.7'
            ' DJANGO_SETTINGS_MODULE=collector.settings')):
        with cd(PROJECT_ROOT):
            run('find . -type f -name \*.pyc -delete')
            run('rm -rf src/gmecol')
            run('pip install -r gmecol_project/requirements.txt')
            run('ln -s ~/prod_settings.py gmecol_project/collector/collector/')
            run('./bin/django-admin.py syncdb --migrate')
            run('./bin/django-admin.py collectstatic --noinput')


def deploy():
    create_build()
    deploy_build()
    restart_memcached()
    restart_apache()
