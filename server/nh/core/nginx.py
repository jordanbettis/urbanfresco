from nh.core.middleware import Middleware

class NginxMiddleware(Middleware):
    """
    The nginx cacher ruins some request variables. This middleware
    fixes them.
    """
    def process_request(self, request):
        request.remote_addr = request.headers.get(
            "X-Real-IP", request.remote_addr)
        request.scheme = request.headers.get(
            "X-Scheme", request.scheme)
        return request
