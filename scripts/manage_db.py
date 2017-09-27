#!/usr/bin/env python
import socket

from migrate.versioning.shell import main
from nh.core.module_loader import load_module

config = load_module("site_config.local.%s" % socket.gethostname())

connect_url = 'postgresql+psycopg2://%(user)s:%(pass)s@%(host)s/%(db)s' \
            % config.DB

repository = "%s/migration" % config.BASE_DIR

if __name__ == '__main__':
    main(url=connect_url, debug='False', repository=repository)
