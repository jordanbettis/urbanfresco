from nh.core import cache
from nh.auth.models import User
from nh.core.templates import found_redirect

def get_user_info(username, session):
    """
    Given a username, return a user.info dict, ensuring it's in the
    memcache.
    """
    info = cache.get("user-info-%s" % username)
    if not info:
        user = session.query(User).filter(
            User.name==username).first()
        if not user:
            return None
        info = user.info
        cache.set("user-info-%s" % username, info, 180)

    return info

def authentication_redirect(request, recent=True):
    """
    Given a request, ensure that the user is authenticated, returning
    either None if it is, or a found_redirect sending the user to the
    login form.
    """
    if recent:
        if not request.user.authenticated_recently:
            return found_redirect(
                request, request.url_for("auth-login", complete=request.path_qs))
    else:
        if not request.user.authenticated:
            return found_redirect(
                request, request.url_for("auth-login", complete=request.path_qs))
    
    return None
