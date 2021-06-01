from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application

# This is useless list
# but it is required for avoiding
# flake8 messages about unused modules
_modules_to_be_used_by_parents = [IOLoop.__name__, RequestHandler.__name__, Application.__name__]
