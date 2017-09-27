#!/usr/bin/env python
from nh.core.app import initialize
from nh.map.projection import get_mmap, get_zoombox, ll_to_xy

import mapnik2 as mapnik
import sys, getopt, re, os

from lxml import etree

initialize()

from nh.core.config import CONFIG

def main():
    params = CONFIG.MAP

    try:
        opts, args = getopt.getopt(sys.argv[1:], "m:c:s:")
    except getopt.GetoptError, error:
        print str(error)
        sys.exit(2)

    ## defaults
    mpp = 4
    ## Corner of LaSalle and Lake
    coords = "N41.88579N,W87.63253"
    params['tile-size'] = 3000
    params['style-template'] = "/mapnik/make_map.xml"

    if args:
        mpp, coords, params['tile-size'] = params_from_svg(args[0])
        order = "lat-lon"

    else:
        for option, argument in opts:
            if option == "-m":
                mpp = int(argument)
            elif option == "-c":
                coords = argument
            elif option == "-s":
                params['tile-size'] = int(argument)

    normal_coords = coords.upper()
    if normal_coords[0] in ["N", "S"]:
        order = "lat-lon"
    else:
        order = "lon-lat"

    normal_coords = normal_coords.replace("N", "")
    normal_coords = normal_coords.replace("E", "")
    normal_coords = normal_coords.replace("S", "-")
    normal_coords = normal_coords.replace("W", "-")

    if order == "lat-lon":
        lat, lon = [float(x) for x in normal_coords.split(",")]
    else:
        lon, lat = [float(x) for x in normal_coords.split(",")]

    width = mpp * params['tile-size']

    print lat, lon, width
    zoombox = get_zoombox(lat, lon, width)
    mmap = get_mmap(params, mpp)
    mmap.zoom_to_box(zoombox)

    center = ll_to_xy(lat, lon)
    
    output = "map-%s--%d.%d.%d.png" % (coords, mpp, center[0], center[1])
    mapnik.render_to_file(mmap, output)
    print "Wrote file to %s" % output

def params_from_svg(fname):
    """
    Get the parameters from an existing svg file
    """
    fd = open(fname)

    print "Updating bitmap for %s" % fname
    
    data = etree.parse(fd)

    root = data.getroot()
    image = root.findall(".//{http://www.w3.org/2000/svg}image")[0]

    size = int(image.get("height"))

    image_xref = image.get(
        "{http://www.w3.org/1999/xlink}href")

    image_fname = os.path.split(image_xref)[1]
    pwd = os.getcwd()
    fd.seek(0)
    fdata = fd.read()
    fd.close()
    fdata = fdata.replace(image_xref, "file://%s/%s" % (pwd, image_fname))
    write_fd = open(fname, "w")
    write_fd.write(fdata)
    write_fd.close()
    

    mpp, center_x, center_y = [
        int(x) for x in image_fname.split(
            "--")[1].split(".")[:-1]]

    coords = re.compile("map-.*--").search(image_xref).group()[4:-2]

    print coords
    
    return mpp, coords, size

    
main()
