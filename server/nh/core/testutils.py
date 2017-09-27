from nh.core.app import CoreApp, initialize
from nh.core import config

from urllib import urlencode
from sys import argv
import StringIO

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import mimetypes

from webob import Request

class MockApp(CoreApp):
    def __init__(self, **kwargs):
        """
        Add the local configuration
        """
        ## If no_cookies is set to true, we won't automatically
        ## transport cookies from responses to future requests.
        ## This is necessary for some auth testing.
        self.no_cookies = kwargs.pop("no_cookies", False)
        if not self.no_cookies:
            self.cookies = dict()
        
        self.environ = get_environ()
        
        super(MockApp, self).__init__(**kwargs)

    def request(self, method, path, **kwargs):
        """
        Make a request of a given method.

        We avoid the parent __call__ so we can return a Response
        object.
        """
        if not self.no_cookies:
            self.environ['HTTP_COOKIE'] = str("; ".join(
                    ["=".join(x) for x in self.cookies.items()]))
        
        environ = dict([(x,y) for x,y in self.environ.items()])
        for key, value in kwargs.items():
            if key.startswith("wsgi_"):
                key = key.replace("wsgi_", "wsgi.")
            environ[key] = value

        environ['REQUEST_METHOD'] = method
        environ['PATH_INFO'] = path

        response = self.process_request(environ)

        ## Pull cookies from the response so subsequent requests
        ## will behave properly, wrt session and csrf
        if not self.no_cookies:
            cookies = [x[1].split(";")[0].split("=") for x \
                           in response.headerlist \
                           if x[0] == "Set-Cookie"]
            self.cookies = dict(self.cookies.items() + cookies)
        return response
        
    def get(self, path, **kwargs):
        """
        Make a get request.
        """
        return self.request("GET", path, **kwargs)

    def post(self, path, data, files=[], **kwargs):
        """
        Make a post request.

        'data' is a dict
        """
        if len(files) != 0:
            mime_objects = []

            for key, value in data.items():
                mime_obj = MIMEText(value, "plain")
                mime_obj.add_header(
                    "content-disposition", "form-data", name=key)
                mime_obj.set_charset("utf-8")
                mime_objects.append(mime_obj)

            for field_name, file_name in files:
                major, minor = mimetypes.guess_type(
                    "default-avatar-profile.jpg")[0].split("/")
                data_fd = open(file_name, "r")
                data = data_fd.read()
                data_fd.close()
                if major == "image":
                    mime_obj = MIMEImage(data, minor, lambda x: x)
                elif major == "application":
                    mime_obj = MIMEApplication(data, minor, lambda x: x)
                elif major == "text":
                    mime_obj = MIMEText(data, minor)
                mime_obj.add_header(
                    "content-disposition", "form-data", name=field_name,
                    filename=file_name)
                mime_objects.append(mime_obj)

            multipart = MIMEMultipart(
                "form-data", None, mime_objects)
            header_offset = multipart.as_string().find("\n\n") + 2
            payload_string = multipart.as_string()[header_offset:]
            kwargs['wsgi_input'] = StringIO.StringIO(payload_string)
            kwargs['CONTENT_TYPE'] = multipart.get("content-type")
            kwargs['CONTENT_LENGTH'] = len(payload_string)
        else:
            encoded_data = dict()
            for key, value in data.items():
                if isinstance(key, unicode):
                    key = key.encode("utf-8")
                if isinstance(value, unicode):
                    value = value.encode("utf-8")
                encoded_data[key] = value
            encoded_data = urlencode(encoded_data)
            kwargs['wsgi_input'] = StringIO.StringIO(encoded_data)
            kwargs['CONTENT_TYPE'] = \
                "application/x-www-form-urlencoded; charset=utf-8"
            kwargs['CONTENT_LENGTH'] = len(encoded_data)

        return self.request("POST", path, **kwargs)

    def login(self, user, session=True):
        """
        Make all subsequent requests with 'user's authentication.

        'session' indiciates if the current browser session flag
        should also be set, which affects "current_auth"
        """
        assert not self.no_cookies, "Cookieless mockapp can't do login"
        assert user.auth_key, "Cowardly refusing login uncommitted user"

        self.cookies['nh-auth'] = user.auth_key
        if session:
            if not user.session_key:
                user.session_key = user.new_session_key()
            self.cookies['nh-session'] = user.session_key
            
def get_environ(**kwargs):
    """
    Return an environment with kwargs added 
    """
    environ = {
        'SCRIPT_NAME': '',
        'REQUEST_METHOD': 'GET',
        'PATH_INFO': '/',
        'SERVER_PROTOCOL': 'HTTP/1.0',
        'QUERY_STRING': '',
        'CONTENT_LENGTH': '0',
        'HTTP_USER_AGENT': 'nh test environ',
        'HTTP_CONNECTION': 'Keep-Alive',
        'SERVER_NAME': '127.0.0.1',
        'REMOTE_ADDR': '127.0.0.1',
        'SERVER_PORT': '80',
        'HTTP_HOST': 'localhost',
        'HTTP_ACCEPT': '*/*',
        'CONTENT_TYPE': '',
        'wsgi.version': (1,0),
        'wsgi.url_scheme': "http",
        'wsgi.input': StringIO.StringIO(),
        'wsgi.errors' : StringIO.StringIO(),
        'wsgi.multithread': False,
        'wsgi.multiprocess': False,
        'wsgi.run_once': False}

    for key, value in kwargs.items():
        if key.startswith("wsgi_"):
            key = key.replace("wsgi_", "wsgi.")
        environ[key] = value

    return environ

