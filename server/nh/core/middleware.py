
from webob import Response

from nh.core.module_loader import load_object
from nh.core.controllers import ControllerLibrary
from nh.core.templates import render_response, moved_redirect, not_found

from routes.util import URLGenerator

class Middleware(object):
    """
    Base class for middleware objects.
    """
    def __init__(self, wrapped_app):
        self.wrapped_app = wrapped_app

    def __call__(self, request, environ):
        result = self.process_request(request)

        # If process_request produced a result object, short circuit 
        if not isinstance(result, Response):
            response = self.process_wrapped(result, environ)

        response = self.process_response(request, response)
        return response

    def process_request(self, request):
        """
        Called before the wrapped application (inner middleware and
        controllers)
        """
        return request

    def process_wrapped(self, request, environ):
        """
        Call the wrapped middleware/controllers.
        """
        return self.wrapped_app(request, environ)
    
    def process_response(self, request, response):
        """
        Called after the wrapped application.
        """
        return response


class ControllerMiddleware(Middleware):
    """
    This is a special middleware which is always present, for
    resolving and calling the controller.
    """
    def __init__(self, config):
        self.controllers = ControllerLibrary(config)

    def process_wrapped(self, request, environ):
        route = self.controllers.match(environ)
        if not route:
            # See if the route would succeed without a trailing '/'
            path_info = request.path_info
            if len(path_info) > 1 and path_info[-1:] == "/":
                environ['PATH_INFO'] = path_info[:-1]
                if self.controllers.match(environ):
                    return moved_redirect(request, path_info[:-1])
            return not_found(request)
        
        controller = route['controller']
        request.route = route
        request.url_for = URLGenerator(self.controllers.routes, environ)
        response = controller(request)

        return response


class MiddlewareLibrary(object):
    def __init__(self, config):
        """
        Load and link all the middlware classes so they're ready to process requests
        """
        middleware_names = config.MIDDLEWARE
        middleware_classes = [load_object(x) for x in middleware_names]

        self.middleware = [
            ControllerMiddleware(config)]

        while len(middleware_classes) > 0:
            cls = middleware_classes.pop()
            self.middleware.append(cls(self.middleware[-1:][0]))

        self.middleware.reverse()

    def __call__(self, request, environ):
        return self.middleware[0](request, environ)
            
                                   
            
            
        
