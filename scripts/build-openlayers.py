#!/usr/bin/env python

import os, sys

from nh.core.app import initialize
initialize()

def main():
    from nh.core.config import CONFIG
    
    output_file = os.path.join(CONFIG.BASE_DIR, "env/static/contrib/OpenLayers.js")
    os.chdir(os.path.join(CONFIG.BASE_DIR, "client/contrib/OpenLayers/build"))
    if CONFIG.DEBUG:
        os.system("python ./build.py -c none full.cfg %s" % output_file)
    else:
        os.system("python ./build.py -c jsmin full.cfg %s" % output_file)

if __name__ == "__main__":
    main()
        
