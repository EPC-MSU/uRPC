import asyncio
import os
import logging

from tornado.platform.asyncio import AsyncIOMainLoop
from tornado.web import Application

from frontend.handler import editor, generic, project
from frontend.util.session import SessionManager

try:
    import settings as Settings
except ImportError:
    class Settings:
        url_prefix = ""
        port = 8888


def make_app():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    fronted_dir = os.path.join(current_dir, "frontend")
    static_dir = os.path.join(fronted_dir, "static")

    settings = {
        "app_root": current_dir,
        "debug": True,
        "compress_response": True,
        "template_path": os.path.join(fronted_dir, "templates"),
        "static_path": static_dir,
        "cookie_secret": "__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
        "static_url_prefix": Settings.url_prefix + r"/static/",
        # "login_url": "/login"
    }

    sessions = SessionManager()

    return Application((
        (Settings.url_prefix + r"/main$", generic.MainHandler, {"sessions": sessions}, "main"),
        (Settings.url_prefix + r"/help(?P<page>[a-z_]+)?$", generic.HelpHandler, {}, "help"),
        (Settings.url_prefix + r"/editor$", editor.EditorHandler, {"sessions": sessions}, "editor"),
        (Settings.url_prefix + r"/project/(?P<action>[a-z_]+)?$",
         project.ProjectHandler, {"sessions": sessions}, "project"),
        (Settings.url_prefix + r"/(?P<action>[a-z_]+)?$", generic.MainHandler, {"sessions": sessions}, "upload")
    ), **settings)


if __name__ == "__main__":
    AsyncIOMainLoop().install()
    app = make_app()

    logging.basicConfig(level=logging.INFO)
    logging.info("Starting server on port {}...".format(Settings.port))
    app.listen(Settings.port, max_buffer_size=100 * 1024 * 1024)
    asyncio.get_event_loop().run_forever()
    # test
