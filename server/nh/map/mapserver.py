from nh.core.config import CONFIG
from nh.core.db import Session
from nh.auth.models import User
from nh.core import cache as memcache
from nh.map.projection import get_envelope, get_cache_filename
from nh.images.models import Image, Collection

from tornado.web import RequestHandler, HTTPError, asynchronous
from tornado.httpclient import AsyncHTTPClient

from sqlalchemy.sql.expression import func, and_

import os, email, time, stat, json
from datetime import datetime
from hashlib import md5

PARAMS = CONFIG.MAP

class MapServer(RequestHandler):
    SUPPORTED_METHODS = ("GET",)

    @asynchronous
    def get(self, overlay, zoom, x, y):
        """
        cat may be 'osm' for the osm base layer, which is handled with
        the OSM_MMAPS array defined above, and the mapnik style.xml
        template.

        It may also be 'nh' for the neighborhoods maps overlay, or it may
        be a user key for an individual user's overlay.
        """
        x, y, zoom = int(x), int(y), int(zoom)

        envelope = get_envelope(PARAMS, x, y, zoom)
        key, has_nh = self.get_cache_info(overlay, envelope)

        if has_nh:
            has_nh_str = "t"
        else:
            has_nh_str = "f"

        filename = get_cache_filename(key)

        if os.path.exists(filename):
            self.serve_file(filename, True, has_nh)
        else:
            port = CONFIG.TILE_MAKER_PORTS[y % len(CONFIG.TILE_MAKER_PORTS)]
            url = "http://localhost:%d/%s/%s/%d/%d/%d/%s.png" % (
                port, overlay, has_nh_str, zoom, x, y, key)
        
            client = AsyncHTTPClient()
            client.fetch(url, self.callback, connect_timeout=60, request_timeout=80)

    def callback(self, response):
        """ The TileMaker call has finished, serve the tile from the cache """
        if response.code != 200:
            raise HTTPError(504, "Tilemaker Failure")
        
        result = json.loads(response.body)

        self.serve_file(result['filename'], result['cached'],
                        result['has_nh'])

    def serve_file(self, filename, cached, has_nh):
        """
        Serve the file and finish the request.
        """
        if cached:
            stat_data = os.stat(filename)
            modified = datetime.fromtimestamp(stat_data[stat.ST_MTIME])
            self.set_header("Last-Modified", modified)
            
            ims_value = self.request.headers.get("If-Modified-Since")
            if ims_value is not None:
                date_tuple = email.utils.parsedate(ims_value)
                if_since = datetime.fromtimestamp(time.mktime(date_tuple))
                if if_since >= modified:
                    self.set_status(304)
                    self.finish()
                    return
        else:
            self.set_header("Last-Modified", datetime.now())

        if has_nh:
            self.set_header("Cache-Control", "must-revalidate")
        else:
            self.set_header("Cache-Control", "public")
            
        cache_fd = open(filename)
        cached_image = cache_fd.read()
        cache_fd.close()

        etag = md5()
        etag.update(cached_image)
        etag_hex = etag.hexdigest()
        self.set_header("Etag", '"%s"' % etag_hex)

        if etag_hex in self.request.headers.get("Etag", ""):
            self.set_status(304)
            self.finish()
            return
        
        self.set_header("Content-Type", "image/png")
        self.set_header("Content-Length", len(cached_image))
        self.write(cached_image)
        self.finish()

    def get_cache_info(self, overlay, envelope):
        """
        This returns the cache key for the given tile, and also if the
        tile contains any neighborhoods.
        """
        keyhash = md5()
        sqlbox = "BOX(%s %s, %s %s)" % envelope
        keyhash.update(sqlbox)

        session = Session()

        has_nh = session.query(Collection.id).filter(
            Collection.way.op("&&")(
                func.setsrid(func.box2d(sqlbox), PARAMS['srid']))).first() \
                is not None

        if has_nh:
            query = session.query(Collection.id).filter(Collection.way.op("&&")(
                    func.setsrid(func.box2d(sqlbox), PARAMS['srid'])))
        
            if overlay != "nh":
                user_id = memcache.get("user-id-%s" % overlay)
                if not user_id:
                    user_id = session.query(User.id).filter(
                        User.name==overlay).first()[0]
                    memcache.set("user-id-%s" % overlay, user_id, 90)
            else:
                user_id = None

            if user_id:
                query = query.filter(Collection.images.any(
                        and_(Image.available==True, Image.user_id==user_id)))
            else:
                query = query.filter(Collection.images.any(Image.available==True))

            filled_ids = query.all()
            keyhash.update(",".join([str(x[0]) for x in filled_ids]))
        
        session.commit()
                       
        cache_key = keyhash.hexdigest()
            
        return cache_key, has_nh
