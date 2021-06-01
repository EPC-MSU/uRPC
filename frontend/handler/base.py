from uuid import uuid4, UUID

from tornado.web import RequestHandler


class BaseRequestHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def get_current_user(self):
        if not self.get_cookie("session_uid"):
            uid = uuid4()
            self.set_cookie("session_uid", str(uid))
            return uid
        return UUID(self.get_cookie("session_uid"))
