from nh.core.controllers import Controller
from nh.core.config import CONFIG

from geoalchemy import WKTSpatialElement
from nh.auth.models import User
from nh.images.models import Image, Collection
from nh.auth.decorators import authentication_required
from nh.core.templates import not_found, moved_redirect, render_response

from webob import Response
import json

from sqlalchemy.sql import func

class LocationController(Controller):
    def get_routes(self):
        return [
            self.make_route("images-features", "/photos/features.json",
                            self.get_features),
            self.make_route(
                "images-manage-location", "/photos/location/{image_key}/manage",
                self.manage_location),
            self.make_route("images-set-location",
                            "/photos/set/location", self.set_location),
            self.make_route("images-set-collection",
                            "/photos/set/collection", self.set_collection),
            self.make_route("images-col-from-coord", "/photos/col-from-coord",
                             self.collection_from_coordinates),
            ]

    def get_features(self, request):
        """ Get GeoJSON data for features  """

        layer = request.GET.get("layer", "nh")
        collections = request.session.query(Collection)
        images = request.session.query(Image)\
            .filter(Image.available==True)\
            .filter(Image.way!=None)

        if layer != "nh":
            images = images.filter(User.name==layer)
                
        if "bbox" in request.GET:
            params = [float(x) for x in request.GET['bbox'].split(",")] + [
                CONFIG.MAP['srid']]
            env = func.st_makeenvelope(*params)
            collections = collections.filter(Collection.way.intersects(env))
            images = images.filter(Image.way.covered_by(env))
        
        features = list()
            
        for collection in collections.all():
            if layer == "nh":
                url = request.url_for("images-list", colid=collection.id,
                                      colkey=collection.url_key)
            else:
                url = request.url_for("images-userlist", map_username=layer,
                                      colid=collection.id,
                                      colkey=collection.url_key)
            features.append(
                {"type": "Feature",
                 "geometry": {
                        "type": "Polygon",
                        "coordinates": collection.way.coords(request.session)},
                 "properties": {
                        "type": "collection",
                        "name": collection.name,
                        "id": collection.id,
                        "url": url}
                 })

        for image in images.all():
            if layer == "nh":
                url = request.url_for(
                    "images-show", colkey=collection.url_key, image_key=image.key)
            else:
                url = request.url_for(
                    "images-usershow", map_username=layer,
                    colkey=collection.url_key, image_key=image.key)
            features.append(
                {"type": "Feature",
                 "geometry": {
                        "type": "Point",
                        "coordinates": image.way.coords(request.session)},
                 "properties": {
                        "type": "image",
                        "key": image.key,
                        "url": url,
                        "thumb": image.url("thumb")}
                 })
                        
        return Response(content_type="application/json", body=json.dumps(
                {"type": "FeatureCollection",
                 "features": features}))

    @authentication_required
    def manage_location(self, request, image_key):
        """ Provide an interface to manage image locations """
        v = request.vars
        v.image = request.session.query(Image).filter(Image.key==image_key).first()
        if not v.image or not v.image.user_id == request.user.id:
            return not_found(request)
        if v.image.way:
            v.coords = v.image.way.coords(request.session)
            v.center = {"x": v.coords[0], "y": v.coords[1], "z": 3}
        else:
            col_center = WKTSpatialElement(request.session.scalar(
                    v.image.collection.way.centroid.wkt)).coords(request.session)
            v.center = {"x": col_center[0], "y": col_center[1], "z": 3}
        
        return render_response("/images/manage-location.html", request)
    
    @authentication_required
    def set_location(self, request):
        """ Given a photograph, set its location """
        image = self._get_image_from_post(request)
        if not image:
            return not_found(request)
        
        x, y = float(request.POST.get('x', 0)), float(request.POST.get('y', 0))
        point = WKTSpatialElement("POINT(%d %d)" % (x, y), CONFIG.MAP['srid'])

        image.way = point

        collection = request.session.query(Collection).filter(
            Collection.way.gcontains(point)).first()

        if collection and collection.id != image.collection_id:
            return Response(content_type="application/json", body=json.dumps(
                    {"changeCollection": True,
                     "from": image.collection.id,
                     "fromName": image.collection.name,
                     "to": collection.id,
                     "toName": collection.name}))
        else:
            return Response(content_type="application/json", body=json.dumps(
                    {"changeCollection": False}))

    @authentication_required
    def set_collection(self, request):
        """
        If setting the location of a photo coordinates in another
        collection, the user may wish to move the photo to that
        collection.
        """
        image = self._get_image_from_post(request)
        if not image:
            return not_found(request)

        collection_id = request.POST.get("to")
        if not collection_id:
            return not_found(request)

        image.collection_id = int(collection_id)

        return Response(content_type="application/json", body=json.dumps(True))

    def _get_image_from_post(self, request):
        """
        Get an image and check that the user has permissions for it.

        Returns the image if everything is ok and None otherwise
        """
        key = request.POST.get("image")
        image = request.session.query(Image).filter(Image.key==key).first()

        if image and not image.user_id == request.user.id:
            return None

        return image
        
    
    def collection_from_coordinates(self, request):
        """
        Given a set of map coordinates, return json for the collection
        id key, and url.
        """
        x, y = int(request.GET.get('x', 0)), int(request.GET.get('y', 0))
        layer = request.GET.get("layer", "nh")
        point = WKTSpatialElement("POINT(%d %d)" % (x, y), CONFIG.MAP['srid'])
        collection = request.session.query(Collection).filter(
            Collection.way.gcontains(point)).first()

        if collection:
            colid = collection.id
            colkey = collection.url_key
            if layer == "nh":
                url = request.url_for("images-list", colid=colid, colkey=colkey)
            else:
                url = request.url_for("images-userlist",
                                      map_username=layer,
                                      colid=colid, colkey=colkey)
        else:
            colid, colkey, url = (None, None, None)

        return Response(content_type="application/json",
                        body=json.dumps({"colid": colid,
                                         "colkey": colkey,
                                         "url": url}))
