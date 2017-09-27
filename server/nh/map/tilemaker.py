from nh.core.config import CONFIG
from nh.map.projection import get_mmap, get_envelope, get_cache_filename

from tornado.web import RequestHandler

import mapnik2 as mapnik

import os, json
from PIL import Image, ImageOps

PARAMS = CONFIG.MAP

class TileMaker(RequestHandler):
    """
    The tilemaker is a server we access asynchronously to request that
    a tile gets created.

    The idea is that there will be a number of TileMaker servers running.
    When the MapServer needs a tile, it will choose which TileMaker is
    responsible for that particular tile, based on its coordinates, and
    request the tile from it.

    When the TileMaker is done generating the tile, it returns the metadata
    in json format. The MapServer can then fetch the image from the
    filesystem.
    """
    SUPPORTED_METHODS = ("GET",)
    
    def get(self, overlay, has_nh, zoom, x, y, key):

        zoom, x, y = int(zoom), int(x), int(y)
        
        envelope = get_envelope(PARAMS, x, y, zoom, PARAMS['gutter'])
        filename = get_cache_filename(key)
        cached = True
        
        if not os.path.exists(filename):
            
            cached = False

            size = (PARAMS['gutter'] * 2 + PARAMS['tile-size'],
                    PARAMS['gutter'] * 2 + PARAMS['tile-size'])
            
            image = mapnik.Image(*size)
            bbox = mapnik.Box2d(*envelope)

            mmap = get_mmap(PARAMS, PARAMS['zoom'][zoom], overlay)
            
            mmap.zoom_to_box(bbox)
            mmap.buffer_size=PARAMS['buffer-size']
            mapnik.render(mmap, image)

            raw_data = image.tostring()
            pil_image = Image.fromstring("RGBA", size, raw_data)
            pil_image = ImageOps.crop(pil_image, border=PARAMS['gutter'])

            pil_image.save(filename, "png")

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({
                    "filename": filename,
                    "overlay": overlay,
                    "zoom": zoom, "x": x, "y": y,
                    "cached": cached,
                    "has_nh": has_nh == "t"}))

