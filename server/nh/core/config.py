
from nh.core import module_loader

## This is assigned a Configuration object by the app.
CONFIG = None

class ConfigurationError(Exception):
    pass

class Configuration(object):
    def __init__(self, path=None):
        """
        Path should be the fully qualified python dot path to a
        settings module.
        """
        if path:
            self.__dict__['_module'] = module_loader.load_module(path)
        else:
            self.__dict__['_module'] = None
            
        self.__dict__['_overrides'] = dict()

    def __getattr__(self, name):
        """
        This permits us to use conf.PARAMETER syntax.
        """
        selfd = self.__dict__

        if selfd['_overrides'].has_key(name):
            return selfd['_overrides'][name]
        elif selfd['_module'] and selfd['_module'].__dict__.has_key(name):
            return selfd['_module'].__dict__[name]
        else:
            raise ConfigurationError(
                "Missing option: %s" % name)

    def __getitem__(self, name):
        """
        And also support conf['PARAMETER']
        """
        return self.__getattr__(name)    
    
    def __setattr__(self, name, value):
        """
        Override config file options
        """
        self.__dict__['_overrides'][name] = value
