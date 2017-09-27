import os
import urllib
from nh.core import config, middleware, templates, db, cache

from webob import Request

import socket

def initialize(config_path=None, config_obj=None, reinitialize=False):
    """
    Perform all tasks necessary to initialize the process state for
    running the application.

    This is designed so that it can be run multiple times with no
    effect after the first, so that mock objects can be initialized
    before the app is created.
    """
    if reinitialize or config.CONFIG is None:
        if config_obj:
            config.CONFIG = config
        elif config_path:
            config.CONFIG = config.Configuration(conf_paths)
        else:
            config.CONFIG = config.Configuration(
                "site_config.local.%s" % socket.gethostname())

        templates.ENV = templates.setup_env(config)
        cache.CACHE = cache.connect(config.CONFIG)
        if os.environ.has_key("NH_UNITTEST_RUN"):
            db.ENGINE = db.connect(config.CONFIG.TEST_DB)
        else:
            db.ENGINE = db.connect(config.CONFIG.DB)

class CoreApp(object):
    def __init__(self, config_path=None, config_obj=None):
        initialize(config_path=config_path, config_obj=config_obj)
        self.middleware = middleware.MiddlewareLibrary(config.CONFIG)

    def process_request(self, environ):
        """
        This is split out of __call__ so we have a place were we can
        access the response object, from a subclassed module.
        """
        request = Request(environ)

        ## Add a template variables object
        request.vars = templates.TemplateVariableLibrary()
        return self.middleware(request, environ)
        
    def __call__(self, environ, start_response):
        response = self.process_request(environ)
        start_response(response.status, response.headerlist)
        return response.body
