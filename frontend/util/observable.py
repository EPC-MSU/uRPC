from asyncio import get_event_loop
from collections import namedtuple, MutableSequence
from itertools import chain
from weakref import WeakSet

InsertEvent = namedtuple("InsertEvent", ["target", "prop", "new"])
DeleteEvent = namedtuple("DeleteEvent", ["target", "prop", "old"])


# AttachEvent = namedtuple("AttachEvent", ["target"])
# DetachEvent = namedtuple("DetachEvent", ["target"])
# UpdateEvent = namedtuple("UpdateEvent", ["target", "prop", "old", "new"])


class EventDispatcher:
    def __init__(self):
        self._observables = {}
        self._loop = get_event_loop()
        self._pending = None

    def register(self, target, processor):
        self._observables[id(target)] = processor
        if not self._pending:
            self._loop.call_soon(self._deliver)

    # def unregister(self, target):
    #     try:
    #         del self._observables[target]
    #     except KeyError:
    #         pass

    def _deliver(self):
        for processor in self._observables.values():
            processor()
        self._observables = {}


# After AST is wrapped in observable proxies it must be manipulated only via them
class Observable:
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher
        self._listeners = WeakSet()

        self._added = set()
        self._deleted = set()

    def _broadcast(self, evt):
        if isinstance(evt, InsertEvent):
            self._added.add(evt)
        elif isinstance(evt, DeleteEvent):
            self._deleted.add(evt)
        self._dispatcher.register(self, self._process)

    def _process(self):
        if len(self._added) == 0 and len(self._deleted) == 0:
            return
        added = self._added - self._deleted
        deleted = self._deleted - self._added
        events = [e for e in chain(added, deleted)]
        # grab strong ref
        listeners = tuple(self._listeners)
        for l in listeners:
            l(events)


class ObservableChildrenNodes(MutableSequence, Observable):
    def __init__(self, wrapped, dispatcher):
        super().__init__(dispatcher)
        self._wrapped = wrapped

    @property
    def node(self):
        return self._wrapped.node

    def __getitem__(self, index):
        return self._wrapped.__getitem__(index)

    def __len__(self):
        return self._wrapped.__len__()

    def insert(self, index, value):
        self._wrapped.insert(index, value)
        new = self._wrapped[index]
        self._broadcast(InsertEvent(self, index, new))

    def __delitem__(self, index):
        old = self._wrapped[index]
        self._wrapped.__delitem__(index)
        self._broadcast(DeleteEvent(self, index, old))

    def __setitem__(self, index, value):
        old = self._wrapped[index] if index in self._wrapped else None
        self._wrapped.__setitem__(index, value)
        new = self._wrapped[index]
        if old:
            self._broadcast(DeleteEvent(self, index, old))
        self._broadcast(InsertEvent(self, index, new))

    def _process(self):
        if len(self._added) == 0 and len(self._deleted) == 0:
            return

        added = self._added - self._deleted
        deleted = self._deleted - self._added
        events = [e for e in chain(added, deleted)]

        current_node = self._wrapped.node
        while current_node:
            listeners = tuple(current_node._listeners)
            for l in listeners:
                l(events)
            current_node = current_node.parent


# class Node:
#     def on(self, listener):
#         return self._listeners.add(listener)
#
#     def off(self, listener):
#         return self._listeners.remove(listener)


# class ObservableMap(MutableMapping, Observable):
#     def __init__(self, wrapped):
#         super().__init__()
#         self._wrapped = wrapped
#
#     def __iter__(self):
#         return self._wrapped.__iter__()
#
#     def __len__(self):
#         return self._wrapped.__len__()
#
#     def __delitem__(self, key):
#         old = self._wrapped[key]
#         self._wrapped.__delitem__(key)
#         self._broadcast(DeleteEvent(self, key, old))
#
#     def __setitem__(self, key, value):
#         old = self._wrapped[key] if key in self._wrapped else None
#         self._wrapped.__setitem__(key, value)
#         new = self._wrapped[key]
#         if old:
#             self._broadcast(DeleteEvent(self, key, old))
#         self._broadcast(InsertEvent(self, key, new))
#
#     def __getitem__(self, key):
#         return self._wrapped.__getitem__(key)


# Mutates original AST!
def wrap(node, dispatcher):
    for k, v in enumerate(node.children):
        node.children[k] = wrap(v, dispatcher)

    # node.children = ObservableList(node.children, dispatcher)

    return node
