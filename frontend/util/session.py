from collections import Container
from os import sep, access, R_OK
from os.path import join, isfile
from uuid import UUID

from tornado.ioloop import IOLoop

from urpc.ast import Protocol
from urpc.storage.json import JsonStorage

try:
    from settings import temp_dir
except ImportError:
    temp_dir = join(sep, "tmp")  # join("tmp") for Windows


class CachedItem:
    def __init__(self, timeout, project):
        self.timeout = timeout
        self.project = project


class SessionManager(Container):
    # after 3 minutes without access project is removed from RAM cache and is dumped to disk
    _dump_timeout = 3 * 60

    def __init__(self):
        self._storage = JsonStorage()
        self._loop = IOLoop.current()
        self._cache = {}

    def _path_from_uid(self, uid):
        file_name = str(uid) + ".json"
        file_path = join(temp_dir, file_name)
        return file_path

    def __getitem__(self, uid):
        assert isinstance(uid, UUID)
        item = self._cache.setdefault(uid, CachedItem(None, None))
        if item.timeout:
            self._loop.remove_timeout(item.timeout)

        if not item.project:
            path = self._path_from_uid(uid)
            if isfile(path) and access(path, R_OK):
                with open(path, "rb") as f:
                    item.project = self._storage.load(f)
            else:
                item.project = Protocol(name="Default project", version="0")

        item.timeout = self._loop.call_later(self._dump_timeout, self._dump_cached, uid)
        return item.project

    def __setitem__(self, uid, project):
        assert isinstance(uid, UUID) and isinstance(project, Protocol)
        item = self._cache.setdefault(uid, CachedItem(None, None))
        if item.timeout:
            self._loop.remove_timeout(item.timeout)
        item.project = project
        item.timeout = self._loop.call_later(self._dump_timeout, self._dump_cached, uid)

    def __contains__(self, uid):
        assert isinstance(uid, UUID)
        if uid in self._cache:
            return True
        else:
            file_name = str(uid) + ".json"
            file_path = join(temp_dir, file_name)
            return isfile(file_path) and access(file_path, R_OK)

    def _dump_cached(self, uid):
        assert isinstance(uid, UUID)
        item = self._cache.pop(uid)
        self._loop.remove_timeout(item.timeout)
        path = self._path_from_uid(uid)
        with open(path, "wb") as f:
            self._storage.save(item.project, f)
