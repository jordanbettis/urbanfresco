
from nh.core import config

def test_load_config():
    conf = config.Configuration("nh.core.test.mock_config")
    config.CONFIG = conf
    from nh.core import config as c
    assert c.CONFIG.OPTION == "test"
    config.CONFIG = None

def test_overrides():
    conf = config.Configuration("nh.core.test.mock_config")
    conf.OPTION2 = 'test2'
    assert conf.OPTION2 == "test2"
    conf.OPTION3 = "test3"
    assert conf.OPTION3 == "test3"
    
def test_failed_lookup():
    conf = config.Configuration("nh.core.test.mock_config")
    try:
        option = conf.XYZZY
    except config.ConfigurationError:
        pass
    else:
        assert False
