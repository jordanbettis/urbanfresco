
from webob import Response
from nh.core.templates import found_redirect

def permission_required(**kwargs):
    """
    This decorator ensures that a user of the given action has the
    correct permission class for the action.

    Args:
     registered: boolean
     verified: boolean
     authenticated: boolean
     authenticated_recently: boolean
     service: string, a Permission object service
    """
    def wrap(action):
        return _permission_required(action, **kwargs)
    return wrap
            
def registration_required(*args, **kwargs):
    """
    Ensures that the user has filled in the username and password form.

    Args:
      redirect: if failure, where should the user be sent? Default is auth/login
    """
    if len(kwargs) > 0:
        def wrap(action):
            return _permission_required(
                action, registered=True, redirect=kwargs.get('redirect'))
        return wrap
    else:
        return _permission_required(args[0], registered=True)

def authentication_required(*args, **kwargs):
    """
    Ensures that the user is logged in. If recent==True, the login
    must have occured recently

    Args:
     recent: requires user.authenaticated_recently
    """
    if len(kwargs) != 0:
        def wrap(action):
            return _permission_required(
                action, authenticated=True,
                authenticated_recently=kwargs.get('recent', False))
        return wrap
    else:
        return _permission_required(args[0], authenticated=True)

def _permission_required(action, **kwargs):
    perm_args = kwargs
    def decorate(self, request, **kwargs):
        if request.user.has_permission(**perm_args):
            return action(self, request, **kwargs)
        else:
            location = request.url_for("auth-login", complete=request.path_qs)
            return found_redirect(request, location)
            
    return decorate
