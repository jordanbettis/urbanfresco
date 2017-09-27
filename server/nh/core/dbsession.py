from nh.core.middleware import Middleware
from nh.core.db import Session

class DatabaseMiddleware(Middleware):
    def process_wrapped(self, request, environ):
        """
        Estabish a session in the request object. Rollback if anything
        goes wrong, otherwise commit.
        """
        session = Session()
        request.session = session
        
        try:
            response = self.wrapped_app(request, environ)
            session.commit()
        except:
            session.rollback()
            raise
        
        return response
