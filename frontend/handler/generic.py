from tornado.httputil import url_concat
from frontend.handler.base import BaseRequestHandler


class MainHandler(BaseRequestHandler):
    def __init__(self, application, request, sessions, **kwargs):
        super().__init__(application, request, **kwargs)
        self._sessions = sessions

    def get(self, action=None):
        protocol = self._sessions[self.current_user]
        self.redirect(url_concat(self.reverse_url("editor"), {"action": "view", "handle": protocol.uid}))


class HelpHandler(BaseRequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def get(self, action=None):
        self.render("help.html")
