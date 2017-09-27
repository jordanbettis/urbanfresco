import pylibmc

CACHE = None

from base64 import b16encode as encode
from hashlib import sha256

def connect(config):
    """
    Returns a usable cache connection.
    """
    return pylibmc.Client(
        config.CACHE_SERVERS, behaviors={"ketama":True, "tcp_nodelay":True})

def sanitize_key(key):
    """ memecache is prickly wrt the values in the key """
    sanitary_key = encode(key)
    if len(sanitary_key) > 244:
        sha = sha256()
        sha.update(sanitary_key)
        sanitary_key = sha.hexdigest()

    return sanitary_key
        

def get(key, *args, **kwargs):
    """
    Get a value, if possible, sanatizing the key
    """
    sanitary_key = sanitize_key(key)
    return CACHE.get(sanitary_key, **kwargs)

def set(key, value, *args, **kwargs):
    """
    Set a value, with a sanatized key
    """
    sanitary_key = sanitize_key(key)
    return CACHE.set(sanitary_key, value, *args, **kwargs)
