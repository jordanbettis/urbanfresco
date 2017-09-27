from lxml import etree
from sys import argv

from nh.core.app import initialize

initialize()

from nh.map.projection import ll_to_xy, xy_to_ll
from nh.core.db import Session
from nh.images.models import Collection
from nh.core.config import CONFIG

from geoalchemy import WKTSpatialElement

from sqlalchemy.sql import func

class PolygonPainter(object):
    def __init__(self, data):
        root = data.getroot()
        image = root.findall(".//{http://www.w3.org/2000/svg}image")[0]
        
        # All our map images are square
        size = float(image.get("height"))

        self.mpp, center_x, center_y = [
            int(x) for x in image.get(
                "{http://www.w3.org/1999/xlink}href").split(
                "--")[1].split(".")[:-1]]

        self.offset_x = float(image.get('x'))
        self.offset_y = float(image.get('y'))

        ## Coordinates of the upper left of the image in map coords
        self.ul_x_map = center_x - (size / 2) * self.mpp;
        self.ul_y_map = center_y + (size / 2) * self.mpp;

    def map_coords(self, svg_x, svg_y):
        """
        Given two svg coordinates, return the map coordinates
        """
        easting = (svg_x - self.offset_x) * self.mpp
        southing = (svg_y - self.offset_y) * self.mpp

        return (self.ul_x_map + easting, self.ul_y_map - southing)

    def paint(self, data):
        """
        Mimic the stroke painting parser in processing the path data,
        but output a list of map coordinates.
        """
        current_pos = (0,0)
        coord_type = "m"

        output = list()

        for datum in data:
            if datum in ["m", "l", "L", "M"]:
                coord_type = datum
            elif datum == "z":
                # Link back to the first node
                output.append(output[0])
            else:
                coord = [float(x) for x in datum.split(",")]
                if coord_type != "l":
                    current_pos = coord

                    if coord_type == "m":
                        coord_type = "l"
                    elif coord_type == "M":
                        coord_type = "L"
                    
                else:
                    current_pos[0] += coord[0] 
                    current_pos[1] += coord[1] 

                output.append(self.map_coords(*current_pos))

        return output

def get_path_data(data):
    """
    Return any neighborhoods in the xml data in the form of a dic
    """
    path_data = {
        'nhoods': list(),
        'labels': list(),
        'label_paths': list(),
        'labels_out': list()
    }
    
    root = data.getroot()
    paths = root.findall(".//{http://www.w3.org/2000/svg}path")
    for path in paths:
        title = path.find(".//{http://www.w3.org/2000/svg}title").text
        desc = path.find(".//{http://www.w3.org/2000/svg}desc")
        painter = PolygonPainter(data)
        way = painter.paint(path.get("d").split(" "))
        if desc is None:
            raise ValueError("No desc for %s" % title)
        else:
            print "Found %s for %s" % (desc.text, title)
        if desc.text == "nh":
            path_data['nhoods'].append((title, way))
        elif desc.text == "label":
            path_data['labels'].append((title, way))
        elif "path" in desc.text:
            if "right" in desc.text:
                direc = str("right")
            elif "left" in desc.text:
                direc = str("left")
            else:
                raise ValueError("No alignment for %s" % title)
            path_data['label_paths'].append((title, way, direc))
        else:
            raise ValueError("Unknown desc %s for %s" % (desc.text, title.text))
        
    return path_data

def main():
    session = Session()
    data = etree.parse(open(argv[1]))
    path_data = get_path_data(data)

    for nhood in path_data['nhoods']:
        obj, created = session.get_or_create(Collection, name=nhood[0])
        if created:
            print "Creating %s" % nhood[0]
        else:
            print "Updating %s" % nhood[0]
            
        obj.way = WKTSpatialElement(
            "POLYGON((%s))" % ", ".join(["%s %s" % x for x in nhood[1]]),
            CONFIG.MAP['srid'])

        ## Don't edit name.multiline if it already exists because it may
        ## have been modified in the database
        if not obj.name_multiline:
            obj.name_multiline = obj.name
            
        obj.max_line_length = max(
            [len(x) for x in obj.name_multiline.split('\n')])
        
    for label in path_data['labels']:
        obj = session.query(Collection).filter(Collection.name==label[0]).first()
        if not obj:
            print "Nhood not found for label: %s " % label[0]
        else:
            obj.label = WKTSpatialElement(
                "LINESTRING(%s)" % ", ".join(["%s %s" % x for x in label[1]]),
                CONFIG.MAP['srid'])
            obj.label_length = func.ST_Length(obj.label)
            print "Label %s updated" % label[0]
            
    for label_path in path_data['label_paths']:
        obj = session.query(Collection).filter(Collection.name==label_path[0]).first()
        if not obj:
            print "Nhood not found for label_path: %s" % label_path[0]
        else:
            obj.label_out_path = WKTSpatialElement(
                "LINESTRING(%s)" % ", ".join(["%s %s" % x for x in label_path[1]]),
                CONFIG.MAP['srid'])
            print "LabelPath %s updated" % label_path[0]
            obj.label_out_align = label_path[2]
            line_end = label_path[1][-1]
            obj.label_out = WKTSpatialElement(
                "POINT(%s)" % "%s %s" % line_end, CONFIG.MAP['srid'])
    
    session.commit()

if __name__ == "__main__":
    main()
