
from webob import Response
import json, os

from jinja2 import TemplateNotFound
from jinja2 import Environment, FileSystemLoader, Markup

## The global environment is created in app.py based on the
## configruation.
ENV = None
    
class TemplateVariableLibrary(dict):
    """
    A dict that allows easy attribute-style variable access.

    Added to the request as request.vars.
    """
    def __setattr__(self, key, val):
        self[key] = val

    def __getattr__(self, key):
        return self.get(key)

def escape_and_break(value):
    """
    Escape all SGML tags from markup, but then add <br>
    to the resultant safe string at newlines
    """
    markup = Markup.escape(value)
    return markup.replace("\n", Markup("<br>\n"))

def setup_env(config):
    """
    To be called from app.py to set the ENV variable
    """
    env = Environment(loader=FileSystemLoader(
            config.CONFIG.TEMPLATE_PATH))
    
    env.filters['tojson'] = lambda data: json.dumps(data)
    env.filters['escapeandbreak'] = escape_and_break

    return env

def get_template(template_name, *args, **kwargs):
    """
    Return a template option from ENV, keeping clients from having
    to mess with the global.
    """
    return ENV.get_or_select_template(template_name, *args, **kwargs)

def render_string(template_name, request=None, variables=dict()):
    """
    Produce a template given either a request with a vars attribute,
    or a variables library.
    """
    template = get_template(template_name)
    if request:
        variables = request.vars
        variables['request'] = request

    return template.render(**variables)

def render_response(template_name, request, status=200, ajax_data={}):
    """
    This is a helper function to switch returning either a normal
    http_response, if the view is being used synchronously, or a
    json response if it's being used via ajax.
    
    The ajax_data should be a json-serializable data
    structure. The response is a webob response object.

    If "template" is not empty, we use the given template to create
    a 'http' attribute on the json data, prefering the -ajax template
    if it exists, or we use it to make the body of a synchronous
    webob response.

    The status of a ajax response is always 200 but we will include a
    'status' attribute in the json
    """
    if "x-ajax" in request.headers:
        ajax_data['status'] = status
        
        if template_name != "":
            # See if there's an ajax-specific template
            nc = os.path.splitext(template_name)
            ajax_tmpl_name = "".join([nc[0], "-ajax", nc[1]])
            
            ajax_data['html'] = render_string(
                [ajax_tmpl_name, template_name], request)
            
        return Response(content_type="application/json",
                        body=json.dumps(ajax_data),
                        request=request)
    else:
        if template_name != "":
            body = render_string(template_name, request)
        else:
            body = ""
        return Response(status=status, request=request, body=body)

def moved_redirect(request, new_path, ajax_data={}):
    """
    Create a response instructing the client to try a different
    path. Mostly for trailing slash redirects.
    """
    response = _get_error_response(request, 301, ajax_data)
    response.headerlist.append(('Location', new_path))
    return response

def found_redirect(request, new_path, ajax_data={}):
    """
    Create a responsey instructing the client to try a different
    path. Mostly for trailing slash redirects.
    """
    response = _get_error_response(request, 302, ajax_data)
    response.headerlist.append(('Location', new_path))
    return response

def not_found(request, ajax_data={}):
    """
    Generate a not-found error response.
    """
    return _get_error_response(request, 404, ajax_data)

def forbidden(request, ajax_data={}):
    """
    Generate a forbidden error response.
    """
    return _get_error_response(request, 403, ajax_data)

def _get_error_response(request, status_code, ajax_data):
    """
    This is used to either render an error html template or return
    a simple string-body request;
    """
    try:
        response = render_response(
            "%d.html" % status_code, request,
            status=status_code, ajax_data=ajax_data)
    except TemplateNotFound:
        response = render_response(
            "", request, status=status_code, ajax_data=ajax_data)
        if response.content_type == "text/html":
            response.content_type = "text/plain"
            response.body = str(response.status)

    return response
