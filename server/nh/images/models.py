from nh.core.db import Base
from nh.core.config import CONFIG

from sqlalchemy import (
    Column, Integer, Unicode, Boolean,
    String, DateTime, ForeignKey,
    PickleType, Float)

from sqlalchemy import func
from sqlalchemy.orm import relationship, backref
from geoalchemy import GeometryColumn, Polygon, Point, LineString, GeometryDDL
from geoalchemy.postgis import PGComparator

from random import choice
from PIL import Image as PILImage

import os

from nh.auth.models import User
from nh.images.utils import wilson_score

class Image(Base):
    __tablename__ = "nh_images_image"
    id = Column(Integer, primary_key=True)

    ## Count of the number of times 'get' has been called
    views = Column(Integer, default=0)

    ## Stored in the database for sorting reasons
    score = Column(Float, default=0)

    ## Used in filenames and urls, "/foo/bar/{key}-small.jpg"
    key = Column(String(29), default=lambda: "".join(
            [choice("0123456789") for x in range(29)]))

    user_id = Column(Integer, ForeignKey("nh_auth_user.id"))
    user = relationship("User", backref="images")

    way = GeometryColumn(
        Point(srid=CONFIG.MAP['srid']), comparator=PGComparator)
        
    ## An image might not be available because it's been deleted
    ## or the upload isn't complete
    available = Column(Boolean, nullable=False, default=False)
    
    ## Has a user indicated that this image is not appropriate?
    flagged = Column(Boolean, nullable=False, default=False)
    ## If an image is flagged and cleared by an admin, it can't be reflagged
    cleared = Column(Boolean, nullable=False, default=False)
    ## If an image is rejected by admin, it's deleted, but we also want to know
    ## that it was caused by administrative action
    rejected = Column(Boolean, nullable=False, default=False)
    ## Special flag for DMCA notices
    copyright_flag = Column(Boolean, nullable=False, default=False)
 
    collection_id = Column(Integer, ForeignKey("nh_images_collection.id"))
    collection = relationship(
        "Collection", backref=backref("images", lazy="dynamic"))
    
    data = Column(PickleType(mutable=True), nullable=False, default=dict())
    
    created = Column(DateTime, nullable=False, default=func.current_timestamp())
    changed = Column(DateTime, nullable=False, default=func.current_timestamp(),
                     onupdate=func.current_timestamp())

    def __repr__(self):
        return u"Image number %d" % self.id

    def url(self, size):
        """ Return a url path """
        if self.available:
            return "%s/%s-%s.jpg" % (CONFIG.IMAGE_URL, self.key, size)
        else:
            return "%s/img/notavail-%s.jpg" % (CONFIG.STATIC_URL, size)

    def info(self, session):
        """
        Return a dictionary of all the info used in displaying the image
        """
        data = {
            'id': self.id,
            'key' : self.key,
            'votes': self.votes.count(),
            'views': self.views,
            'score': self.score,
            'available': self.available,
            'description': self.data.get("description", None)}

        if self.available:
            data['ratio'] = float(self.data['size'][0])/float(self.data['size'][1]),
        else:
            ## The ratio of the not-available images
            data['ratio'] = 4.0/3.0

        if self.way:
            data['way'] = self.way.coords(session)

        for x, y, name in CONFIG.IMAGE_SIZES:
           data[name] = self.url(name)

        if self.collection_id:
            data['collection_name'] = self.collection.name
            data['collection_id'] = self.collection.id
            data['collection_url_key'] = self.collection.url_key
            
        if self.user_id:
            data['user_id'] = self.user_id
            data['user_name'] = self.user.name
            data['user_display_name'] = self.user.display_name
            for size in CONFIG.AVATAR_SIZES:
                data["user_%s_avatar" % size[2]] = self.user.avatar_url(size[2])
            
        return data

    @property
    def upload_path(self):
        return os.path.join(
            CONFIG.UPLOAD_DIR, "%s%s" % (self.key, self.data['upload-ext']))

    def generate_sizes(self):
        """
        Generate an image for each configured size
        """
        img_obj = PILImage.open(self.upload_path)

        self.data['size'] = img_obj.size
        
        for size in CONFIG.IMAGE_SIZES:
            img_obj.thumbnail((size[0], size[1]), PILImage.ANTIALIAS)
            img_obj.save(os.path.join(CONFIG.IMAGE_DIR, "%s-%s.jpg" % (
                        self.key, size[2])))

    def unlink_sizes(self):
        """
        Delete the sized images. 
        """
        for size in CONFIG.IMAGE_SIZES:
            try:
                os.unlink(os.path.join(CONFIG.IMAGE_DIR, "%s-%s.jpg" % (
                            self.key, size[2])))
            except OSError:
                pass

    def calculate_score(self):
        """
        Return the score for this image as a number from 0 to 1
        """        
        total_votes = self.votes.count()
        up_votes = self.votes.filter(Vote.up==True).count()
        return wilson_score(up_votes, total_votes)
                        
GeometryDDL(Image.__table__)

class Collection(Base):
    """
    A collection is 1) a polygon which 2) contains Images.
    """
    __tablename__ = "nh_images_collection"
    id = Column(Integer, primary_key=True)

    ## Doesn't have to be unique, used for display purposes.
    name = Column(Unicode(200), nullable=False)
    ## Name with optional newlines inserted, for display on the map
    name_multiline = Column(Unicode(200))
    ## Length of the longest line in map_multiline
    max_line_length = Column(Integer)

    way = GeometryColumn(
        Polygon(srid=CONFIG.MAP['srid']), comparator=PGComparator)

    ## A line on the map 
    label = GeometryColumn(
        LineString(srid=CONFIG.MAP['srid']), comparator=PGComparator)
    label_out_path = GeometryColumn(
        LineString(srid=CONFIG.MAP['srid']), comparator=PGComparator)
    label_out = GeometryColumn(
        Point(srid=CONFIG.MAP['srid']), comparator=PGComparator)
    label_out_align = Column(String(5))
    label_length = Column(Integer, default=0)
    
    data = Column(PickleType(mutable=True), nullable=False, default=dict())

    created = Column(DateTime, nullable=False, default=func.current_timestamp())
    changed = Column(DateTime, nullable=False, default=func.current_timestamp(),
                     onupdate=func.current_timestamp())

    def get_url_key(self):
        """
        Return name suitable for including in a url.
        """
        return "%s-chicago" % self.name.lower().replace(" ", '-')
    url_key = property(get_url_key)

    def __repr__(self):
        return u"Collection for %s" % self.name

GeometryDDL(Collection.__table__)

class Vote(Base):
    """
    This represents a vote for a photo by a user.
    """
    __tablename__ = "nh_images_vote"
    id = Column(Integer, primary_key=True)

    up = Column(Boolean, nullable=False, default=True)
    
    user_id = Column(Integer, ForeignKey("nh_auth_user.id"))
    user = relationship("User", backref=backref("votes", lazy="dynamic"))

    image_id = Column(Integer, ForeignKey("nh_images_image.id"))
    image = relationship("Image", backref=backref("votes", lazy="dynamic"))

    created = Column(DateTime, nullable=False, default=func.current_timestamp())
