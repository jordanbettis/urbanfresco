from nh.core.middleware import Middleware
from nh.core import cache
from nh.auth.models import User
from nh.auth.userlog import log

from sqlalchemy.orm.exc import NoResultFound

import random

class UserMiddleware(Middleware):
    def process_request(self, request):
        cookieless = False
        auth_key = request.cookies.get("nh-auth", None)
        session_key = request.cookies.get("nh-session", None)
        
        if auth_key is None:
            cookieless=True
            auth_key = cache.get("%s:%s" % (
                    request.user_agent, request.remote_addr))

        try:
            if cookieless:
                user = request.session.query(User).filter_by(
                    auth_key=auth_key, registered=False).one()
            else:
                user = request.session.query(User).filter_by(
                    auth_key=auth_key).one()
        except NoResultFound:
            user = User()
            request.session.add(user)
            request.session.commit()
            log("new-user", user, [request.user_agent, request.remote_addr])
            cache.set("%s:%s" % (request.user_agent, request.remote_addr),
                      user.auth_key, time=90)

        user.current_auth = (
            session_key != None and session_key == user.session_key)

        request.user = user

        log("request", user, [request.remote_addr,
                              request.url, request.referer])

        return request
        
    def process_response(self, request, response):
        auth_key = request.cookies.get("nh-auth", None)
        if auth_key != request.user.auth_key:
            response.set_cookie("nh-auth", request.user.auth_key)

        return response
