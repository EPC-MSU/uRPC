from tornado.httputil import url_concat
from version import BUILDER_VERSION
from frontend.handler.base import BaseRequestHandler


class MainHandler(BaseRequestHandler):
    def __init__(self, application, request, sessions, **kwargs):
        super().__init__(application, request, **kwargs)
        self._sessions = sessions

    def get(self, action=None):
        protocol = self._sessions[self.current_user]
        self.redirect(url_concat(self.reverse_url("editor"), {"action": "view", "handle": protocol.uid}))


class HelpHandler(BaseRequestHandler):
    pages = {
        "general": "О проекте",
        "creation": "Создание проекта",
        "library": "Библиотека",
        "doc": "Документация",
        "firmware": "Прошивка",
        "qt": "Qt debugger",
        "python": "Python",
        "csharp": "C#",
        "tango": "TANGO",
        "profiles": "Конвертер профилей"
    }

    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)

    def get(self, page=None):
        if page not in self.pages:
            page = "general"
        self.render(f"help_{page}.html", pages=self.pages, version=BUILDER_VERSION, page=page)
