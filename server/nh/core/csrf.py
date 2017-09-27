from middleware import Middleware
from nh.core.config import CONFIG

from hashlib import sha224

from jinja2 import Markup

def csrf_exempt(action):
    """
    View to mark an action as being except from csrf checks.
    """
    def func(*argc, **argv):
        return action(*argc, **argv)
    func.csrf_exempt = True
    return func

def make_token(user):
    """ Make a token for a given user """
    csrf_token = sha224()
    csrf_token.update("%s%s%s" % (
            CONFIG.SECRET, user.auth_key, user.session_key))
    return csrf_token.hexdigest()

def generate_token_printer(token):
    """ Make a token printer to be used in the templates """
    def print_token(format="form"):
        if format == "form":
            return Markup(
                u'<input type="hidden" name="csrftoken" value="%s">' % token)
        if format == "plain":
            return unicode(token)
    return print_token

class CsrfMiddleware(Middleware):
    """
    This middleware must go inside of the auth middleware.

    It configures the request to validate against the csrf check in
    the Controller object.

    It also adds the CSRF key generator to request.vars
    """
    def is_safe(self, request):
        """ Is the HTTP method one defined to be 'safe' by the standard? """
        return request.method in ["GET", "HEAD", "TRACE", "OPTIONS"]

    def has_valid_header(self, request):
        """ Does the request have a valid X-CSRFToken? """
        user_token = request.user.data.get('csrf-token')
        return (user_token and user_token == request.headers.get("x-csrftoken"))

    def has_post_key(self, request):
        """ Does the request have a valid key in its post data? """
        user_token = request.user.data.get('csrf-token')
        if "csrftoken" in request.POST:
            form_token = request.POST.pop("csrftoken")
            return (user_token and user_token == form_token)
        return False
    
    def process_request(self, request):
        token = request.user.data.get("csrf-token")
        if token is None:
            token = make_token(request.user)
            request.user.data['csrf-token'] = token
        request.vars.csrf_token = generate_token_printer(token)

        if self.is_safe(request) \
                or self.has_valid_header(request) \
                or self.has_post_key(request):
            request.csrf_cleared = True
        else:
            request.csrf_cleared = False

        return request

