from nh.core.testutils import MockApp, initialize
from nh.core import db, config, testutils, controllers

from webob import Request, Response
from nh.auth.models import User

from nh.auth.tests.fixtures import users

def setup():
    global SESSION, USERS
    initialize()
    mc = "nh.auth.tests.test_middleware.MockController"
    if mc not in config.CONFIG.CONTROLLERS:
        config.CONFIG.CONTROLLERS.insert(-1, mc)
    print config.CONFIG.CONTROLLERS
    SESSION = db.Session()
    USERS = users.get_fixtures()
    users.add_fixtures(SESSION, USERS)

def teardown():
    users.delete_fixtures(SESSION, USERS)
    SESSION.commit()

class MockController(controllers.Controller):
    def get_routes(self):
        return [
            self.make_route("check-user", "/check-user", self.check_user)]

    def check_user(self, request):
        response = Response(status=200, request=request, body="")
        response.user_key = request.user.auth_key
        return response
    
def test_loggedin():
    app = MockApp()
    sup = SESSION.query(User).filter_by(name=u"sup").one()
    app.login(sup)
    response = app.get("/check-user")
    print config.CONFIG.CONTROLLERS
    print response
    assert response.user_key == sup.auth_key, "login falure"

def test_cookieless():
    app = MockApp(no_cookies=True)
    u1 = app.get("/check-user").user_key
    u2 = app.get("/check-user").user_key

    app.environ['REMOTE_ADDR'] = "127.0.0.3"

    u3 = app.get("/check-user").user_key

    app.environ['REMOTE_ADDR'] = "127.0.0.1"

    u4 = app.get("/check-user").user_key

    assert u1 == u2 == u4, "cookieless users unequal"

    assert u1 != u3, "cookieless user equal"

def test_session():
    app = MockApp()
    sup = SESSION.query(User).filter_by(name=u"sup").one()
    
