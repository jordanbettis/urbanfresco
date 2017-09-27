"""
Generate urls to image files based on settings
"""
from nh.core.config import CONFIG

def _format(key, size):
    return "%s/%s-%s.jpg" % (CONFIG.IMAGE_URL, self.key, size)

def thumb_url(key):
    return _format(key, "thumb")

def view_url(key):
    return _format(key, "view")

def max_url(key):
    return _format(key, "max")
    
