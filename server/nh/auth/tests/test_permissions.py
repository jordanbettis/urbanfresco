from datetime import datetime, timedelta

from nh.core.testutils import MockApp, initialize
from nh.core import db, config, testutils, controllers

from webob import Response
from nh.auth.models import User
from nh.auth.decorators import (
    registration_required, authentication_required, permission_required)
from nh.auth.tests.fixtures import users

def setup():
    global SESSION, USERS
    initialize()
    mc = "nh.auth.tests.test_permissions.MockController"
    if mc not in config.CONFIG.CONTROLLERS:
        config.CONFIG.CONTROLLERS.insert(-1, mc)
    SESSION = db.Session()
    USERS = users.get_fixtures()
    users.add_fixtures(SESSION, USERS)

def teardown():
    users.delete_fixtures(SESSION, USERS)
    SESSION.commit()

class MockController(controllers.Controller):
    def get_routes(self):
        return [
            self.make_route("reg-required", "/reg-required", self.reg_required),
            self.make_route("reg-required", "/reg-required-redir", self.reg_required_redir),
            self.make_route("auth-required", "/auth-required", self.auth_required),
            self.make_route("recent-required", "/recent-auth-required", self.recent_auth_required),
            self.make_route("verif-required", "/verif-required", self.verif_required),
            self.make_route("xyzzy-required", "/xyzzy-required", self.xyzzy_required),
            ]
    @registration_required
    def reg_required(self, request):
        return Response(body="reg-required")
    @registration_required(redirect="/redir")
    def reg_required_redir(self, request):
        return Response(body="reg-required-redir")
    @authentication_required
    def auth_required(self, request):
        return Response(body="auth-required")
    @authentication_required(recent=True)
    def recent_auth_required(self, request):
        return Response(body="recent-auth-required")
    @permission_required(verified=True)
    def verif_required(self, request):
        return Response(body="verif-required")
    @permission_required(service="xyzzy")
    def xyzzy_required(self, request):
        return Response(body="xyzzy-required")

def test_super():
    app = MockApp()
    sup = SESSION.query(User).filter_by(
        email=u"sup@neighborhoods.chicago.il.us").one()
    app.login(sup, session=False)
    SESSION.commit()

    response = app.get("/xyzzy-required")
    print response
    assert response.status_int == 302, 'no session superuser failure'

    app.login(sup, session=True)
    SESSION.commit()
    response = app.get("/verif-required")
    assert response.status_int == 200, "superuser perm failure"
    response = app.get("/xyzzy-required")
    assert response.status_int == 200, "superuser perm failure"
    
def test_anon():
    app = MockApp()
    response = app.get("/reg-required")
    assert response.status_int == 302, 'anon allowed for reg'
    response = app.get("/reg-required-redir")
    assert "login" in response.location, 'redir failed'
    response = app.get("/auth-required")
    assert response.status_int == 302, 'anon allowed for auth'
    response = app.get("/verif-required")
    assert response.status_int == 302, 'anon allowed for verif'
    response = app.get("/xyzzy-required")
    assert response.status_int == 302, 'anon allowed for xyzzy'

def test_registered():
    app = MockApp()
    reg = SESSION.query(User).filter_by(
        email=u"reg@neighborhoods.chicago.il.us").one()
    app.login(reg)
    SESSION.commit()
    
    response = app.get("/reg-required")
    assert response.status_int == 200, 'reg failed reg'
    response = app.get("/auth-required")
    assert response.status_int == 200, 'reg failed auth'
    response = app.get("/recent-auth-required")
    assert response.status_int == 200, 'reg failed recent auth'
    response = app.get("/verif-required")
    assert response.status_int == 302, "reg allowed for verif"
    response = app.get("/xyzzy-required")
    assert response.status_int == 200, "reg failed for xyzzy"

    reg.last_auth = datetime.now() - timedelta(days=5)
    SESSION.commit()
    response = app.get("/recent-auth-required")
    assert response.status_int == 302, 'recent auth allowd for old login'
