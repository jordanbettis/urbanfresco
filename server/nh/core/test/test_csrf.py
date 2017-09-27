from nh.core.csrf import csrf_exempt
from nh.core.controllers import Controller
from nh.core import templates, db, testutils, config

from nh.auth.models import User

from webob import Response

def setup():
    global SESSION
    testutils.initialize()
    mc = "nh.core.test.test_csrf.MockController"
    if mc not in config.CONFIG.CONTROLLERS:
        config.CONFIG.CONTROLLERS.insert(-1, mc)
    SESSION = db.Session()

class MockController(Controller):
    def get_routes(self):
        return [
            self.make_route("exempt", "/exempt", self.exempt),
            self.make_route("validate", "/validate", self.validate),
            self.make_route("token", "/token", self.token)]

    @csrf_exempt
    def exempt(self, request):
        return Response(body="exempt")

    def validate(self, request):
        return Response(body="validate")

    def token(self, request):
        return Response(body=request.vars.csrf_token())

def test_token():
    user = User()
    SESSION.add(user)
    SESSION.commit()

    app = testutils.MockApp()
    app.login(user)

    response = app.get("/token")
    assert "csrftoken" in response.body
    SESSION.refresh(user)
    assert user.data.has_key("csrf-token")
    assert user.data['csrf-token'] in response.body

def test_exempt():
    app = testutils.MockApp()

    response = app.post("/exempt", {})
    assert response.status_int == 200

    response = app.post("/validate", {})
    assert response.status_int == 403

    response = app.get("/token")
    assert response.status_int == 200
    
    response = app.post("/token", {})
    assert response.status_int == 403

def test_validate():

    user = User()
    SESSION.add(user)
    SESSION.commit()

    app = testutils.MockApp()
    app.login(user)
    
    response = app.get("/validate")
    SESSION.refresh(user)
    key = user.data['csrf-token']

    response = app.post("/validate", {'csrftoken': key})
    print response
    assert response.status_int == 200

    response = app.post("/validate", {}, HTTP_X_CSRFTOKEN=key)
    assert response.status_int == 200
