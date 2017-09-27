""" Test the core.controllers module """

from nh.core.controllers import Controller, ControllerLibrary
from nh.core.config import Configuration

from nh.core.testutils import get_environ

from webob import Request
from routes import Mapper

def test_no_controllers():
    config = Configuration()
    config.CONTROLLERS = []

    controllers = ControllerLibrary(config)

    assert controllers.controllers == []

    assert controllers.match(get_environ()) == None

    
def test_controller():
    cont = Controller()
    try:
        cont.get_routes()
    except AssertionError:
        pass
    else:
        assert False


class MockController(Controller):
    def get_routes(self):
        return [
            self.make_route("foo", "/", self.foo),
            self.make_route("bar", "/xyzzy", self.bar, nothing="happens")]
        
    def foo(self, request):
        return "foo"

    def bar(self, request, nothing=None):
        return nothing

def test_controllers():
    config = Configuration()
    config.CONTROLLERS = [
        'nh.core.test.test_controllers.MockController']
    cont = ControllerLibrary(config)

    request = Request(get_environ())
    request.csrf_cleared=True
    request.route = cont.match(get_environ())
    result = request.route['controller'](request)
    assert result == "foo"

    request = Request(get_environ(PATH_INFO="/xyzzy"))
    request.csrf_cleared=True
    request.route = cont.match(get_environ(PATH_INFO="/xyzzy"))
    result = request.route['controller'](request)
    assert result == "happens"

