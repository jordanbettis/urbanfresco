from nh.core.controllers import Controller
from nh.core.templates import (
    render_response, render_string, not_found, moved_redirect, forbidden)
from nh.core.config import CONFIG
from nh.core import cache 

from nh.auth.models import User
from nh.auth.utils import get_user_info
from nh.auth.decorators import authentication_required
from nh.auth.services import MANAGE_IMAGES

from nh.images.models import Image, Collection, Vote
from nh.images.utils import make_json_info

from wtforms import fields, validators
from wtforms.form import Form

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.types import Numeric
from sqlalchemy.sql.expression import desc, cast
from sqlalchemy.sql import func, and_, or_

from webob import Response
from random import choice

import json, os, math

def username_condition(environ, match):
    """
    Don't resolve a username from a key that doesn't match our
    username rules.
    """
    map_user = match.get('map_username')
    if not map_user:
        return False 
    if len(map_user) < 4:
        return False
    if map_user in CONFIG.BANNED_USERNAMES:
        return False

    return True

class ImageViewer(Controller):
    def get_routes(self):
        return [
            self.make_route("images-put", "/photos/{colid}/put", self.put),
            self.make_route("images-get", "/photos/get", self.get),
            self.make_route("images-vote", "/photos/vote", self.vote),
            self.make_route("images-delete", "/photos/delete", self.delete),

            self.make_route(
                "images-list", "/photos/{colkey}/list/{colid}", self.list),
            self.make_route(
                "images-show", "/photos/{colkey}/show/{image_key}", self.list),
            self.make_route(
                "images-usershow",
                "/photos/{map_username}/{colkey}/show/{image_key}", self.list),
            self.make_route("images-root", "/", self.list),
            self.make_route("images-userroot", "/{map_username}", self.list,
                            conditions={'function': username_condition}),
            self.make_route(
                "images-userlist", "/photos/{map_username}/{colkey}/list/{colid}",
                self.list),
            self.make_route("images-best", "/photos/best", self.list,
                            special="best"),
            self.make_route("images-newest", "/photos/newest", self.list,
                            special="newest"),
            self.make_form_route("images-description", "/photos/description",
                                 "/images/description.html", self.Description),
            ]

    def list(self, request, special=None, map_username=None,
             image_key=None, colkey=None, colid=None):
        """
        This is the main UI view of this application. Loaded with the
        images-list url, it displays the images in a collection in
        list view, with the images-root url, it serves as the document
        root of the site, displaying the map. For images-userview it
        displays a user's root list. Finally, for images-userlist it
        displays a collection list filtered by user.

        Note that colkey exists for SEO purposes to ensure the name of
        the neigobhrood ends up in the URL, we always include and use
        the colid for fetching the collection.
        """
        v = request.vars
        v.collection = None
        v.special = special

        if hasattr(colid, "isdigit") and colid.isdigit():
            v.collection = request.session.query(Collection).get(colid)
            if not v.collection:
                return not_found(request)

        if image_key:
            v.image = request.session.query(Image)\
                .filter(Image.key==image_key).first()
            v.collection = v.image.collection
            colkey = v.collection.url_key
            
        if v.collection:
            if colkey != v.collection.url_key:
                return moved_redirect(request, request.url_for(
                    "images-list", colid=v.collection.id,
                    colkey=v.collection.url_key))
            
        if map_username:
            if map_username != map_username.lower():
                return moved_redirect(request, request.url_for(
                        "images-list", map_username=map_username,
                        colkey=colkey, colid=colid))
            v.user_info = get_user_info(map_username.lower(), request.session)
            if not v.user_info:
                return not_found(request)
            v.show_user_controls = request.user.authenticated and \
                v.user_info['id'] == request.user.id

        v.images = self._get_images(request.session, special == "newest",
                                    v.collection, v.user_info)
        v.jsvars =  self._list_jsvars(request)
        
        return render_response("/images/list.html", request, ajax_data=v.jsvars)

    def _list_jsvars(self, request):
        """
        Create a dict of variables used by the javascript from the
        list view.
        """
        tv = request.vars
        jv = dict()

        if 'l' in request.GET:
            coords = request.GET["l"].split(",")
            try:
                jv['center'] = {
                    'x': float(coords[0]),
                    'y': float(coords[1]),
                    'z': int(coords[2])}
            except ValueError:
                pass

        if 'user_info' in tv and tv['user_info']:
            jv['userName'] = tv.user_info['name']
            jv['userDisplayName'] = tv.user_info['display_name']
            jv['layerName'] = tv.user_info['name']
            jv['baseViewPath'] = request.url_for(
                'images-userroot', map_username=tv.user_info['name'])
            jv['showUserControls'] = tv.show_user_controls
        else:
            jv['layerName'] = 'nh'
            jv['baseViewPath'] = request.url_for('images-root')

        if 'collection' in tv and tv['collection']:
            jv['collectionId'] = tv.collection.id
            jv['collectionName'] = tv.collection.name
            
            if 'user_info' in tv:
                jv['collectionPath'] = request.url_for(
                    'images-userlist', map_username=tv.user_info['name'],
                    colkey=tv.collection.url_key, colid=tv.collection.id)
            else:
                jv['collectionPath'] = request.url_for(
                    'images-list', colkey=tv.collection.url_key,
                    colid=tv.collection.id)
        else:
            if tv.special:
                if tv.special == "newest":
                    jv['order'] = "newest"
            else:
                first_image = tv.images.first()
                if first_image:
                    jv['sliderInitImage'] = first_image.key

        if 'image' in tv and tv['image']:
            jv['imageKey'] = tv.image.key

        return jv

    def _get_images(self, session, newest=False, collection=None, user_info=None):
        """
        Return the set of images for a collection listing
        """
        images_query = session.query(Image).filter(Image.available==True)
        if collection:
            images_query = images_query.filter(Image.collection_id==collection.id)
        if user_info:
            images_query = images_query.filter(Image.user_id==user_info["id"])

        if newest:
            return images_query.order_by(desc(Image.id))
        else:
            ## Ordering by ID is for when images all have the same score
            return images_query.order_by(desc(Image.score), desc(Image.id))
        
        
    @authentication_required(recently=True)
    def put(self, request, colid):
        """
        Upload an image file.
        """
        collection = request.session.query(Collection).get(colid)
        if collection is None:
            return not_found(request)

        file_field = request.POST['files[]']
        
        key = "".join([choice("0123456789") for x in range(29)])
            
        image = Image(key=key, user=request.user, collection=collection)

        image.data = {'upload-filename': file_field.filename,
                      'upload-type': file_field.type,
                      'upload-type-options': file_field.type_options,
                      'upload-ext': os.path.splitext(file_field.filename)[1]}
        
        upload_fd = open(image.upload_path, "w")
        upload_fd.write(file_field.file.read())
        upload_fd.close()

        image.generate_sizes()

        image.available = True
        
        response_data = [
                {"name": "%s.jpg" % key,
                 "url": image.url("view"),
                 "thumbnail_url": image.url("thumb"),
                 "show_url": request.url_for(
                    "images-show", colkey=collection.url_key, image_key=image.key),
                 "delete_url": request.url_for("images-delete", key=key),
                 }]

        image.views = 1
        vote = Vote(user=request.user, image=image, up=True)
        request.session.add(image)
        request.session.add(vote)
        image.score = image.calculate_score()
        return Response(content_type="application/json",
                        body=json.dumps(response_data))

    @authentication_required(recently=True)
    def delete(self, request):
        """
        Delete a photograph
        """
        key = request.POST.get("key", None)
        if not key:
            return not_found(request)
        
        image = request.session.query(Image).filter(Image.key==key).first()
        if not image:
            return not_found(request)

        if image.user.id != request.user.id and not \
                user.has_permission(service=MANAGE_IMAGES):
            return forbidden(request)
        
        image.available = False
        image.data['deleted'] = datetime.now()

        image.unlink_sizes()

        info = image.info(request.session)
        # Reset the cached info to avoid referencing the now unlinked
        # images.
        cache.set("image-info-%s" % str(key), info, 90)

        return Response(content_type="application/json",
                        body=make_json_info(info, request.session))

    def get(self, request):
        """
        Return image info given key(s)

        The supported GET parameters are:
        keys: A comma-separated list of keys to fetch
        previous, next: Booleans indicating if the previous
              and next 16 keys should be returned
        user_name: A filter on the previous and next attributes,
              to narrow the list to just images from the given user
        collection_id: The same, to filter previous and next to
              a given collection
        """
        rdata = request.GET
        keys = rdata.get('keys', "").split(",")
        if keys[0] == "":
            return not_found(request)

        images_info = get_images_info(keys, request.session)

        if images_info and rdata.get('previous', False):
            images_info[0]['previous'] = self._get_keys(
                "previous", images_info[0], request)
        if images_info and rdata.get('next', False):
            images_info[-1]['next'] = self._get_keys(
                "next", images_info[-1], request)

        for info in images_info:
            info['user_url'] = request.url_for(
                "images-userroot", map_username=info['user_name'])
            if "user_name" in rdata:
                info['url'] = request.url_for(
                    "images-usershow", map_username=info['user_name'],
                    colkey=info['collection_url_key'], image_key=info['key'])
                info['collection_url'] = request.url_for(
                    "images-userlist", colkey=info['collection_url_key'],
                    colid=info['collection_id'], map_username=info['user_name'])
            else:
                info['url'] = request.url_for(
                    "images-show", colkey=info['collection_url_key'],
                    image_key=info['key'])
                info['collection_url'] = request.url_for(
                    "images-list", colkey=info['collection_url_key'],
                    colid=info['collection_id'])
            info['editable'] = (
                request.user.authenticated and (
                    info['user_name'] == request.user.name or 
                    request.user.has_permission(service=MANAGE_IMAGES)))
            info['votable'] = request.session.query(Vote)\
                .filter(Vote.user_id==request.user.id)\
                .filter(Vote.image_id==info['id'])\
                .filter(Vote.up==True).count() < 1
            info["location_url"] = request.url_for(
                "images-manage-location", image_key=info['key'])
            info["utils_url"] = request.url_for(
                "staticpage-manage-image", key=info['key'])
                             
            ## We don't really want anybody to see the db keys
            del info['id']
            del info['user_id']

        # Do an insertion sort to ensure the images are the same order
        # as the keys
        images_info_sorted = [None for x in keys]
        for image in images_info:
            images_info_sorted[keys.index(image['key'])] = image

        
        if request.GET.get("count", False):
            table = Image.__table__
            request.session.bind.execute(table.update().where(
                    table.c.key.in_(keys)).values(views = 1 + table.c.views))
                
        return Response(content_type="application/json",
                        body=json.dumps(images_info_sorted))

    def _get_keys(self, direction, image_info, request):
        """
        Return a list of keys starting either before
          or after the image in image_info
        direction is "previous" or "next"

        The limit is 16, because this seems like more
        than we'd ever want in one call. 
        """
        rdata = request.GET
        
        cache_key = "image-%s-%s-%s-%s" % (
            direction, image_info['key'], rdata.get("user_name", ""),
            rdata.get("collection_id", ""))
        keys = cache.get(cache_key)

        #if keys:
        #    return keys
        
        keys_query = request.session.query(Image.key).filter(
            Image.available == True)
        
        if "user_name" in rdata:
            user = get_user_info(rdata['user_name'], request.session)
            if not user:
                return not_found(request)
            keys_query = keys_query.filter(Image.user_id==user['id'])
            
        if "collection_id" in rdata and rdata['collection_id'].isdigit():
            keys_query = keys_query.filter(
                Image.collection_id==int(rdata['collection_id']))

        score = image_info['score']
        image_id = image_info['id']

        if rdata.get("order", "best") == "newest":
            if direction == "previous":
                keys_query = keys_query.filter(Image.id > image_id).order_by(Image.id)
            elif direction == "next":
                keys_query = keys_query.filter(Image.id < image_id).order_by(desc(Image.id))
        else:
            if direction == "previous":
                keys_query = keys_query.filter(
                    or_(func.round(cast(Image.score, Numeric), 13) >
                        func.round(score, 13),
                        and_(func.round(cast(Image.score, Numeric), 13)
                             == func.round(score, 13), Image.id > image_id)))\
                             .order_by(Image.score, Image.id).limit(16)
            elif direction == "next":
                keys_query = keys_query.filter(
                    or_(func.round(cast(Image.score, Numeric), 13) <
                        func.round(score, 13),
                        and_(func.round(cast(Image.score, Numeric), 13)
                             == func.round(score, 13), Image.id < image_id)))\
                             .order_by(desc(Image.score), desc(Image.id)).limit(16)

        keys = keys_query.all()

        if len(keys) != 0:
            keys = [x[0] for x in keys]

        cache.set(cache_key, keys, 90)
        return keys
    
    def vote(self, request):
        """
        If the user likes the photo they can vote for it.

        The values are POST data in the form
          {"image_key": vote(bool)}

        If there are no upvotes at all, then no downvotes are counted either.

        A vote hit is always counted as an image view, even when there are
        no downvotes.
        """
        data = dict([(k, (v.lower() in ['true', 't']))\
                         for k, v in request.POST.items()])

        # all referenced images
        images = request.session.query(Image)\
            .filter(Image.key.in_(data.keys())).all()

        ## We only count up/down votes if the user has upvoted at least one
        ## image this cycle.
        if True in data.values():
            upvoted_image_keys = [x[0] for x in data.items() if x[1]]
            voted_image_keys = request.session.query(Image.key)\
                .filter(Vote.user_id==request.user.id)\
                .filter(Image.key.in_(upvoted_image_keys))\
                .filter(Vote.up==True).all()
            
            for key, value in data.items():
                if not key in voted_image_keys:
                    image = [i for i in images if i.key==key][0]
                    vote, created = request.session.get_or_create(
                        Vote, user=request.user, image_id=image.id)
                    if vote.up != value:
                        vote.up = value

        return Response(content_type="application/json", body=json.dumps(True))

    class Description(Form):
        """ Change the photographer's description of the photograph """
        description = fields.TextField("Description")

        @classmethod
        def permission(cls, request):
            """
            Insert the image in the request so we don't have to fetch it twice
            """
            auth = authentication_redirect(request, recent=False)
            if auth is not None:
                return auth
            
            key = request.GET.get("key", None)
            if not key:
                return not_found(request)
        
            request.image = request.session.query(
                Image).filter(Image.key==key).first()
            if not request.image:
                return not_found(request)

            if request.image.user.id != request.user.id and not \
                    user.has_permission(service=MANAGE_IMAGES):
                return forbidden(request)
                
            return None

        @classmethod
        def initialize_get(cls, request):
            return cls(description=request.image.data.get('description', ""))

        def save(self, request):
            image = request.image
            image.data['description'] = self.description.data
            cache.set("image-info-%s" % str(image.key),
                      image.info(request.session), 90)
            return found_redirect(
                request, request.url_for(
                    'images-usershow', map_username=image.user.name,
                    colkey=image.collection.url_key, image_key=image.key),
                ajax_data={"description": request.image.data['description']})
    
def get_images_info(keys, session):
    """
    Where keys are a list of image keys, return the image_info dict
    rfom each
    """
    #images = [cache.get("image-info-%s" % str(key)) for key in keys]
    images = [None for key in keys]

    keys_for_db = list()
    for i, info in enumerate(images):
        if info is None:
            keys_for_db.append(str(keys[i]))

    if keys_for_db:
        db_images = session.query(Image).filter(
            Image.key.in_(keys_for_db)).all()

        for image in db_images:
            info = image.info(session)
            images[keys.index(image.key)] = info
            cache.set("image-info-%s" % str(key), info, 90) 
            
    return images
                

