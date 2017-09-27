from routes.route import Route
from webob import Response

from nh.core.controllers import Controller
from nh.core.config import CONFIG
from nh.core.templates import render_response, not_found

import mimetypes

class StaticPage(Controller):
    def get_routes(self):
        """
        The page data should be a list of lists with the
        following scheme:

        ["page_name", "url", "template_name"]
        """
        page_routes = [
            self.make_route(x[0], x[1], self.staticpage,
                            template_name=x[2])
            for x in CONFIG.STATIC_PAGES]
        
        return page_routes

    def staticpage(self, request, template_name=""):
        """
        Return a static page by rendering a template
        """
        request.vars.config = CONFIG
        return render_response(template_name, request)

class StaticFile(Controller):
    """
    Return files from the file system, for testing purposes
    """
    def get_routes(self):
        """
        The STATIC_DIRS should be a two-tuple in the form:
        ('url_path', 'filesystem_path')
        """
        return [
            self.make_route(
                None, "%s/{filename:.*?}" % d[0],
                self.staticfile, directory=d[1])
            for d in CONFIG.STATIC_DIRS]

    def staticfile(self, request, directory, filename):
        try:
            fd = open("%s/%s" % (directory, filename))
        except IOError:
            return not_found(request)

        mimetype = mimetypes.guess_type(filename)[0]

        if not mimetype:
            mimetype = "application/octet-stream"

        return Response(status=200, body=fd.read(), mimetype=mimetype)
