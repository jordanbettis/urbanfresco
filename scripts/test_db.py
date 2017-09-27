"""
This script manages the setup and teardown of the test database
for the fab run_tests command.

The user must exist but the database must not exist.
"""
import socket
from os import system

from migrate.versioning import api
from nh.core.module_loader import load_module

from sys import argv

config = load_module("site_config.local.%s" % socket.gethostname())
connect_url = 'postgresql+psycopg2://%(user)s:%(pass)s@%(host)s/%(db)s' \
    % config.TEST_DB

if argv[1] == "setup":

    print "Creating database %s" % connect_url
    system('createdb "%s" -O "%s"' % (
            config.TEST_DB['db'], config.TEST_DB['user']))
    system('createlang plpgsql %s' % config.TEST_DB['db'])
    system('psql -d %s < %s' % (config.TEST_DB['db'], config.POSTGIS_SQL))
    system('psql -d %s < %s' % (config.TEST_DB['db'], config.SRS_SQL))
    system('echo "alter table spatial_ref_sys owner to %s" | psql -d %s ' % (
            config.TEST_DB['user'], config.TEST_DB['db']))
    system('echo "alter table geometry_columns owner to %s" | psql -d %s ' % (
            config.TEST_DB['user'], config.TEST_DB['db']))

    repository = "%s/migration" % config.BASE_DIR

    api.version_control(connect_url, repository)
    api.upgrade(connect_url, repository)

elif argv[1] == "teardown":
    print "Destroying database %s" % connect_url
    system('dropdb "%s"' % config.TEST_DB['db'])
