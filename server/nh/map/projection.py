from math import pi, degrees, radians, cos, sin, atan, sinh, log
from nh.core.templates import get_template
import mapnik2 as mapnik
import os

# Parameters of WSG84 ellipsoid
SEMI_MAJOR = 6378137.0
FLATTENING = 298.257223563
SEMI_MINOR = SEMI_MAJOR * (1 - 1 / FLATTENING)

def ll_to_xy(lat, lon):
    """
    Return a google mercator x/y value given a lat/lon
    """
    x = radians(lon) * SEMI_MAJOR
    y = log((1 + sin(radians(lat))) / cos(radians(lat))) * SEMI_MAJOR
    # Since x/y are in meters, floats are false precision 
    return (int(x), int(y))

def xy_to_ll(x, y):
    """
    Return lon/lat given google mercator x/y
    """
    lon = degrees(x / SEMI_MAJOR)
    lat = degrees(atan(sinh(y/SEMI_MAJOR)))
    return (lat, lon)

def get_mmap(params, meters_per_pixel, overlay="nh"):
    """
    Return a mapnik map object based on the parameters dict from settings
    """
    size = (params['gutter'] * 2 + params['tile-size'],
            params['gutter'] * 2 + params['tile-size'])

    mmap = mapnik.Map(*size)

    # Compile the template for the style file
    style_temppath = "/tmp/mapnik_style_%d.xml" % os.getpid()
    style_template = get_template(params['style-template'])

    ## How many pixels wide is a meter?
    params['meters_per_pixel'] = meters_per_pixel
    params["meters"] = 1.0 / meters_per_pixel
    params['overlay'] = overlay
    
    output = style_template.render(**params)
    style_fd = open(style_temppath, "w")
    style_fd.write(output)
    style_fd.close()

    mapnik.load_map(mmap, style_temppath)

    mmap.srs = params['srs']
    
    os.unlink(style_temppath)

    return mmap

def between(x, l, u):
    """
    Ensure that x is between l and u
    """
    x = max(x,l)
    x = min(x,u)
    return x

def get_zoombox(lat, lon, width):
    """
    Given a latitude, longitude, and width in meters, return
    a mapnik bbox centered on the lat/long width pixels wide.
    """
    center = ll_to_xy(lat, lon)
    offset = width / 2
    lower_left = (center[0] - offset, center[1] - offset)
    upper_right = (center[0] + offset, center[1] + offset)
    bbox = mapnik.Box2d(*(lower_left + upper_right))
    return bbox

def get_envelope(params, x, y, zoom, gutter=None):
    """
    Return the bounding box in the form (lx, ly, ux, uy)

    If a "gutter" parameter is provided, the envelope will include a
    border around the specified bbox which is as wide as the specified
    gutter.
    """
    origin = params['origin']
    size = params['tile-size']
    scale = params['zoom'][zoom]
    offset = (float(x) * size * scale, float(y) * size * scale)
    lower_left = (origin[0] + offset[0], origin[1] + offset[1])
    upper_right = (lower_left[0] + size * scale, lower_left[1] + size * scale)
    if gutter:
        lower_left = tuple([n - (gutter * scale) for n in lower_left])
        upper_right = tuple([n + (gutter * scale) for n in upper_right])
    return lower_left + upper_right

def get_cache_filename(key):
    """
    Return the fully qualified cache filename given a key
    """
    from nh.core.config import CONFIG

    filename = "map-%s.png" % key
    return os.path.join(CONFIG.MAP['cache-dir'], filename)
