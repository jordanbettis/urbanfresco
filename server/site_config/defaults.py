
from os import path

## The base directory of this repository
BASE_DIR = __file__[:__file__.find("/server/site_config")]

MIDDLEWARE = [
    'nh.core.nginx.NginxMiddleware',
    'nh.core.dbsession.DatabaseMiddleware',
    'nh.auth.middleware.UserMiddleware',
    'nh.core.csrf.CsrfMiddleware',
    ]

## ImageViewer should be last since it contains a wildcard match.
CONTROLLERS = [
    "nh.core.staticpage.StaticPage",
    "nh.auth.controllers.UserController",
    "nh.images.location.LocationController",
    "nh.feedback.controllers.FeedbackController",
    "nh.images.controllers.ImageViewer", #### <-- MUST BE LAST
    ]

TEMPLATE_PATH = [
    "%s/templates" % BASE_DIR,
    ]

STATIC_PAGES = [
    ["staticpage-about", "/about", "/staticpages/about.html", 'public'],
    ["staticpage-coppa", "/coppa", "/staticpages/coppa.html", 'public'],
    ["staticpage-jsconfig", "/sys/config.js",
     "/staticpages/jsconfig.js", 'private'],
    ["staticpage-manage-image", "/photos/manage",
     "/staticpages/manage-image.html", 'private'],
    ]

## This blocks possible user names from being created,
## which may conflict with parts of the site
##
## WARNING: Before you ban a username, make sure it's not already in
## use.
BANNED_USERNAMES = [
    'img', 'isrv', 'photo', 'photos', 'map',
    'tms', 'sys', 'static'] + [x[1].split("/")[1] for x in STATIC_PAGES]

STATIC_DIR = path.join(BASE_DIR, "env/static")
STATIC_URL = "/static"

DB = {
    "user": "nh",
    "pass": "nh",
    "host": "localhost",
    "db": "nh"}

TEST_DB = {
    "user": "nh",
    "pass": "nh",
    "host": "localhost",
    "db": "nh_test"}

# Which tcp ports should the daemons liten on? Each
# port number listed results in a process being
# created.
APP_SERVER_PORTS = [9200, 9201, 9202, 9203]
TILE_MAKER_PORTS = [9300, 9301, 9302, 9303]

MAP={
    'tile-size': 256,
    'gutter': 256,
    'style-template': "/mapnik/style.xml",
    'coastline': path.join(BASE_DIR, "dat/chicago.shp"),
    'buffer-size': 1024,
    'srs': "+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 " \
        "+y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over",
    'zoom': [64, 32, 16, 8, 4, 2, 1],
    'min': (-9852314, 5062473),
    'max': (-9693102, 5205572),
    'srs-name': "EPSG: 900913",
    'srid': 900913,
    'origin': (-9852314, 5062473),
    'default-center': {'x': -9757746, 'y': 5145668, 'z': 1},
    'cache-dir': "%s/env/cache" % BASE_DIR,
    'db': DB
     }

## Location of database initialization files
POSTGIS_SQL = "/usr/share/postgresql/9.1/contrib/postgis-1.5/postgis.sql"
SRS_SQL = "/usr/share/osm2pgsql/900913.sql"

MAPSERVER_URL = "/tms"

LOG_DIR = path.join(BASE_DIR, "env/log")

CACHE_SERVERS=["127.0.0.1"]
    
SECRET = "FKDDI08jRgxe6CHtW4MH8YMLMukRIs9ZhZNGC0Dw8QBb88HXKIbjszFE5ofcAG66"

EMAIL_FROM = "Neighborhoods Project Admin <nh@hafd.org>"

# Where are images uploaded?
UPLOAD_DIR = path.join(BASE_DIR, "env/upload")
# From where are they served?
IMAGE_DIR = path.join(BASE_DIR, "env/srv")
# What is the url path?
IMAGE_URL = "/isrv"

## Sizes must go largest to smallest
IMAGE_SIZES = (
    (1200, 900, 'max'),
    (800, 600,  'view'),
    (160, 120, 'thumb'),)

AVATAR_SIZES = (
    (200, 200, 'profile'),
    (50, 50, 'tiny'),)

## Maximum file size we allow in bytes
MAX_UPLOAD_SIZE = 4194304

NH_CLIENT_APP = {
    'base-dir': path.join(BASE_DIR, 'client/nh'),
    'files': ['nh.js',
              'map.js',
              'collection.js',
              'utils.js',
              'location.js',
              'manage-image.js',
              'slide-widget.js',
              'ready.js'
              ]
    }

CONTRIB_APP = {
    'base-dir': path.join(BASE_DIR, 'client/contrib'),
    'files': ['jquery-1.7.1.js',
              'jquery-ui-1.8.18/ui/jquery.ui.widget.js',
              'jquery-file-upload-186a1c2/js/jquery.iframe-transport.js',
              'jquery-file-upload-186a1c2/js/jquery.fileupload.js',
              'swipe.js',
              ]
    }
