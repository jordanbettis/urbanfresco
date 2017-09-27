from routes.route import Route
from webob import Response

from nh.core.controllers import Controller
from nh.core.config import CONFIG
from nh.core.templates import render_response

class StaticPage(Controller):

    def __init__(self):
        self.page_data = CONFIG.STATIC_PAGES
    
    def get_routes(self):
        """
        The pagedata file should be a json list of lists with the
        following scheme:

        ["page_name", "url", "template_name"]
        """
        page_routes = [
            self.make_route(x[0], x[1], self.staticpage,
                            template_name=x[2])
            for x in self.page_data]
        
        return page_routes

    def staticpage(self, request, template_name=""):
        return render_response(template_name, request)
        
