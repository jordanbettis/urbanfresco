
from nh.core.db import Base
from nh.core import config

from datetime import datetime, date, timedelta
from PIL import Image as PILImage

import random, os

import hashlib

from sqlalchemy import (
    Column, Integer, Unicode, Boolean,
    String, Enum, DateTime, ForeignKey,
    PickleType, Date)

from sqlalchemy import func
from sqlalchemy.orm import relationship
from sqlalchemy.orm.interfaces import MapperExtension

def new_auth_key():
    """ Generate and return a new auth key. """
    return _random_value(64)

class User(Base):
    __tablename__ = "nh_auth_user"
    id = Column(Integer, primary_key=True)
    
    auth_key = Column(
        String(64), index=True, nullable=False, default=new_auth_key)
    session_key = Column(String(32))
    
    name = Column(Unicode(200), unique=True)
    email = Column(Unicode(200), unique=True)
    password = Column(String(64))

    dob = Column(Date())
    
    permissions = relationship("Permission", backref="user",
                               primaryjoin="User.id==Permission.user_id")

    ## Automatically has permission for everything
    superuser = Column(Boolean, nullable=False, default=False)
    ## Has filled out name/password form
    registered = Column(Boolean, nullable=False, default=False)
    ## Has clicked the email link
    verified = Column(Boolean, nullable=False, default=False)
    ## Hasn't explicitly logged out since the last login
    authenticated = Column(Boolean, nullable=False, default=False)
    ## Has authenticated this browser session
    current_auth = Column(Boolean, nullable=False, default=False)

    last_auth = Column(DateTime)

    associations = relationship("UserAssociation",
                                backref="to_user",
                                primaryjoin="UserAssociation.to_user_id==User.id",
                                lazy="dynamic")

    data = Column(PickleType(mutable=True), nullable=False, default=dict())
                     
    created = Column(DateTime, nullable=False, default=func.current_timestamp())
    changed = Column(DateTime, nullable=False, default=func.current_timestamp(),
                     onupdate=func.current_timestamp())

    def __repr__(self):
        return u"User %s:%s, [%s], %s %s" % (
            str(self.id), self.auth_key[:8],
            ", ".join(self.flags()), self.email, self.name)

    def flags(self):
        """ Return a list of char flags for the various boolean """
        return [x[1] for x in (
                (self.superuser, 's'),
                (self.registered, 'r'),
                (self.verified, 'c'),
                (self.authenticated, 'a'),
                (self.current_auth, 'A'),) if x[0]]
    
    def has_permission(self, **kwargs):
        """
        Verifies if the user has a permission for the service
        specified by 'service'
        """
        if self.superuser and self.current_auth:
            return True
        elif kwargs.get('registered', False) and not self.registered:
            return False
        elif kwargs.get('verified', False) and not self.verified:
            return False
        elif kwargs.get('authenticated', False) and not self.authenticated:
            return False

        service = kwargs.get("service", None)

        if service:
            if len([perm for perm in self.permissions if perm.service == service]) > 0:
                if kwargs.get("authenticated_recently", False):
                    return self.authenticated_recently
                else:
                    return True
            else:
                return False

        if kwargs.get("authenticated_recently", False):
            return self.authenticated_recently
        else:
            return True

    @property
    def authenticated_recently(self):
        """
        Has the user authenticated this browser session within the
        past day?
        """
        yesterday = datetime.now() - timedelta(hours=24)
        if self.current_auth and self.last_auth and \
                self.last_auth >= yesterday:
            return True
        else:
            return False

    def new_auth_key(self):
        """
        We need new-auth-key in global scope for the declarative above, but
        we also want it as part of the object for clients.
        Gefnerate and return a new auth key.
        """
        return _random_value(64)

    def new_session_key(self):
        """ Generate and return a new session key. """
        return _random_value(32)
    
    def authenticate(self, password):
        """ Returns if 'password' corresponds to the user's password """
        if not self.password:
            return False

        prot, salt, user_hash = self.password.split(":")

        check_hash = hashlib.sha224()
        check_hash.update(salt + password)
        return user_hash == check_hash.hexdigest()

    def set_password(self, password):
        """ Assign 'password' to be user's new password """
        new_salt = _random_value(5)

        new_hash = hashlib.sha224()
        new_hash.update(new_salt + password)
        self.password = "s:%s:%s" % (new_salt, new_hash.hexdigest())

    def login(self, request, password):
        """
        Login a user to a request object. Note that this will cause
        the request.user to be associated with this user.

        Returns a boolean indicating success or failure.
        """
        if not self.authenticate(password):
            return False

        if hasattr(request, "user"):
            if not request.user.registered:
                user_assoc = UserAssociation(
                    from_user=request.user, why="login")
                self.associations.append(user_assoc)

        self.authenticated = True
        self.current_auth = True
        self.last_auth = datetime.now()
        request.user = self

        return True

    def logout(self):
        """
        Log a user out
        """
        self.authenticated = False
        self.current_auth = False
        self.session_key = self.new_session_key()

    @property
    def under_thirteen(self):
        """
        Test if the user is under thirteen, for COPPA compliance

        Return value will be:
          True: If the user is under thirteen
          False: If the user is over thirteen
          None: If the user's age is unknown.
        """
        if not self.dob:
            return None
        
        thirteen = date.today() - timedelta(days=(365 * 13))
        return self.dob >= thirteen

    @property
    def display_name(self):
        """
        Create a printable name for the user
        """
        if "display-name" in self.data and "caps-name" in self.data:
            return u"%s (%s)" % (self.data['display-name'], self.data['caps-name'])
        elif "display-name" in self.data and self.name:
            return u"%s (%s)" % (self.data['display-name'], self.name)
        elif self.name:
            return self.name
        else:
            return u"Anonymous"

    @property
    def info(self):
        """ Return a set of commonly accessed attributes, for the cache """
        info = {
            'id': self.id,
            'auth_key': self.auth_key,
            'name': self.name,
            'verified': self.verified,
            'profile': self.data.get("profile"),
            'display_name': self.display_name}
        for size in config.CONFIG.AVATAR_SIZES:
            info["%s_avatar" % size[2]] = self.avatar_url(size[2])
        return info

    @property
    def avatar_upload_path(self):
        if not "avatar-key" in self.data or not "avatar-ext" in self.data:
            return None
        else:
            return os.path.join(
                config.CONFIG.UPLOAD_DIR, "%s%s" % (
                    self.data['avatar-key'], self.data['avatar-ext']))

    def avatar_url(self, size):
        """ Return the url for the avatar of the given size """
        if not "avatar-key" in self.data:
            return "%s/img/default-avatar-%s.jpg" % (
                config.CONFIG.STATIC_URL, size)
        else:
            return "%s/%s-%s.jpg" % (
                config.CONFIG.IMAGE_URL, self.data['avatar-key'], size)

    def generate_avatar_sizes(self):
        """ Generate avatar image sizes """
        img_obj = PILImage.open(self.avatar_upload_path)
        for size in config.CONFIG.AVATAR_SIZES:
            img_obj.thumbnail((size[0], size[1]), PILImage.ANTIALIAS)
            img_obj.save(os.path.join(config.CONFIG.IMAGE_DIR, "%s-%s.jpg" % (
                        self.data['avatar-key'], size[2])))

    def unlink_avatar(self):
        """
        Delete avatar image as well as sizes
        """
        if self.avatar_upload_path is None:
            return 
        
        try:    
            os.unlink(self.avatar_upload_path)
        except OSError:
            pass
      
        for size in config.CONFIG.AVATAR_SIZES:
            try:
                os.unlink(os.path.join(config.CONFIG.IMAGE_DIR, "%s-%s.jpg" % (
                            self.data['avatar-key'], size[2])))
            except OSError:
                pass

        del self.data['avatar-key']            

class Permission(Base):
    __tablename__ = "nh_auth_permission"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("nh_auth_user.id"))
    service = Column(String(20), nullable=False)
        
    created = Column(DateTime, nullable=False, default=func.current_timestamp())

    def __repr__(self):
        return u"Permission %s for %s" % (self.service, self.user)

class UserAssociation(Base):
    """ This allows us to associate two users """
    __tablename__ = "nh_auth_userassociation"
    id = Column(Integer, primary_key=True)
    to_user_id = Column(Integer, ForeignKey("nh_auth_user.id"))
    why = Column(String(10), nullable=False)
    
    from_user_id = Column(Integer, ForeignKey("nh_auth_user.id"))
    from_user = relationship(
        "User", backref="from_associations",
        primaryjoin="User.id==UserAssociation.from_user_id")
    
    created = Column(DateTime, nullable=False, default=func.current_timestamp())
    
def _random_value(length):
    """ Used above to make keys and salts """
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    return "".join([random.choice(alphabet + alphabet.upper() + '0123456789')
                   for x in range(length)])
