#!/usr/bin/env python
"""
pre-render all tiles at all zoom levels, so the testing server isn't crap
"""
from nh.core.testutils import MockApp, initialize
from nh.map.projection import get_mmap, get_zoombox

import mapnik2 as mapnik
import sys, getopt

initialize()

from nh.core.config import CONFIG

def main():
    params = CONFIG.MAP
    app = MockApp()

    for zoom in enumerate(params['zoom']):
        for x in range(abs(params['max'][0] - params['min'][0])
                       / (zoom[1] * params['tile_size']) + 1):
            for y in range(abs(params['max'][1] - params['min'][1])
                           / (zoom[1] * params['tile_size']) + 1):
                print "Getting tile (%d,%d) for level %d" % (x, y, zoom[0])
                response = app.get("/tms/osm/%d/%d/%d.png" % (zoom[0], x, y))
                print response

main()
