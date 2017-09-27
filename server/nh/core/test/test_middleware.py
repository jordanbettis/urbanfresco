""" Test the core.controllers module """

from nh.core.controllers import Controller
from nh.core.middleware import Middleware, \
    ControllerMiddleware, MiddlewareLibrary
from nh.core.config import Configuration

from nh.core import templates

from nh.core.testutils import get_environ
from jinja2 import Environment, FileSystemLoader

from webob import Request, Response
from routes import Mapper

def setup_package():
    templates.OLD_ENV = templates.ENV
    templates.ENV = Environment(loader=FileSystemLoader("/"))

def teardown_package():
    templates.ENV = templates.OLD_ENV

def test_no_middleware():
    config = Configuration()
    config.CONTROLLERS = []
    config.MIDDLEWARE = []

    middleware = MiddlewareLibrary(config)
    assert len(middleware.middleware) == 1

class MockMiddleware(Middleware):
    def process_request(self, request):
        request.process_request = True
        return request

    def process_wrapped(self, request, environ):
        request.process_wrapped = True
        return request

    def process_response(self, request, response):
        response.process_response = True
        return response
    
def test_middleware():
    mid = MockMiddleware(None)
    response = mid(Request(get_environ()), get_environ())

    assert hasattr(response, "process_request")
    assert hasattr(response, "process_wrapped")
    assert hasattr(response, "process_response")


class MockController(Controller):
    def get_routes(self):
        return [
            self.make_route("foo", "/foo", self.foo)]
        
    def foo(self, request):
        return Response(body="xyzzy")

def test_controller_middleware():
    config = Configuration()
    config.MIDDLEWARE = []
    config.CONTROLLERS = [
        'nh.core.test.test_middleware.MockController']

    cm = ControllerMiddleware(config)

    env = get_environ(PATH_INFO="/foo")
    request = Request(env)
    request.csrf_cleared = True
    response = cm(request, env)

    assert response.body == "xyzzy"

    env = get_environ(PATH_INFO="/nothing")
    request = Request(env)
    request.vars = dict()
    request.csrf_cleared = True
    response = cm(request, env)

    assert response.status_int == 404

    env = get_environ(PATH_INFO="/foo/")
    request = Request(env)
    request.csrf_cleared = True
    response = cm(request, env)

    assert response.status_int == 301

class MockMiddleware2(Middleware):
    pass
    
def test_middleware_library():
    config = Configuration()
    config.MIDDLEWARE = [
        'nh.core.test.test_middleware.MockMiddleware2']
    config.CONTROLLERS = [
        'nh.core.test.test_middleware.MockController']

    ml = MiddlewareLibrary(config)

    assert len(ml.middleware) == 2

    env = get_environ(PATH_INFO="/foo")
    request = Request(env)
    request.csrf_cleared = True
    response = ml(Request(env), env)

    assert response.body == "xyzzy"
