
from routes import Mapper
from routes.route import Route

from nh.core.module_loader import load_object
from nh.core.templates import (
    forbidden, render_string, render_response)

from wtforms.validators import ValidationError
from webob import Response

import json, os

class Controller(object):
    """
    The controller is a callable object which turns a request object
    into a response object.
    """
    def get_routes(self):
        """
        Child classes should return a list of routes.
        """
        assert False, "Controller has no routes"

    def make_route(self, name, path, action, **kwargs):
        """
        Returns a three-tuple containing the arguments needed for
        mapper.connect().
        """
        kwargs['controller'] = self
        kwargs['action'] = action
        return (name, path, kwargs)

    def make_form_route(self, name, path, template_name, FormClass, **kwargs):
        """
        This function exists to remove a lot of the boilerplate
        involved in form processing.

        The Form subclass must have a 'save' method defined, which
        operates on the validated form and view arguments and does
        whatever must be done, returning a WebOb response. If you need
        to kick an error back out to the form, set the error in
        v.errors and raise a wtform ValidationError.

        It must also provide a classwide 'permission' function which
        should return None if there are no permission problems with
        the request, or a HttpResponse object (presumably a 403) that
        is passed back to the client

        You may also provide a classwide 'initialize_get' and
        'initialize_post', functions, which will be used to
        create the form instead of the default constructor. An
        optional 
        """
        def func(request, *args, **kwargs):
            v = request.vars
            v.errors = list()

            failure_response = FormClass.permission(request, *args, **kwargs)
            if failure_response is not None:
                return failure_response
            
            if request.method == "POST":
                if hasattr(FormClass, "initialize_post"):
                    v.form = FormClass.initialize_post(request, *args, **kwargs)
                else:
                    v.form = FormClass(request.POST)
                    
                if v.form.validate():
                    try:
                        result = v.form.save(request, *args, **kwargs)
                        if result is not None:
                            return result
                    except ValidationError as error:
                        v.errors.append(error.message)
            else:
                if hasattr(FormClass, "initialize_get"):
                    v.form = FormClass.initialize_get(request, *args, **kwargs)
                else:
                    v.form = FormClass()

            return render_response(template_name, request)

        return self.make_route(name, path, func, **kwargs)

    def check_csrf(self, request, action):
        """
        Verify that the request has cleared the csrf check.

        This will fail if the view isn't csrf_exempt and the
        middleware hasn't run.
        """
        if hasattr(action, "csrf_exempt") and action.csrf_exempt:
            return True
        elif hasattr(request, "csrf_cleared") and request.csrf_cleared:
            return True
        else:
            return False
        
    def __call__(self, request):
        """
        Given a request with a route object as a member, return a
        response object by calling the appropriate action.
        """
        controller = request.route.pop("controller")
        action = request.route.pop("action")
        if not self.check_csrf(request, action):
            return forbidden(request)
        else:
            return action(request, **request.route)


class ControllerLibrary(object):
    def __init__(self, config):
        self.routes = Mapper()
        self.controllers = list()
        for controller_name in config.CONTROLLERS:
            controller_class = load_object(controller_name)
            controller = controller_class()
            routes = controller.get_routes()
            for route in routes:
                self.routes.connect(route[0], route[1], **route[2])
            self.controllers.append(controller)

    def match(self, environ):
        """
        Return the route matching the data from environ. Note that the
        route will contain controller and action objects.
        """
        route = self.routes.match(environ=environ)
        return route

