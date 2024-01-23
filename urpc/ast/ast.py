import re
from abc import ABCMeta
from collections.abc import MutableMapping, MutableSequence
from typing import Optional
from uuid import uuid4

from urpc.util.idhash import IdentityHash


# Abstract protocol syntax is represented as polytree
class AstNode(IdentityHash, metaclass=ABCMeta):
    class Description(MutableMapping):
        codes = {"english", "russian"}

        def __init__(self, **kwargs):
            self._langs = {}
            for code in self.codes:
                self._langs[code] = kwargs[code] if code in kwargs else ""

        def __iter__(self):
            return self._langs.__iter__()

        def __len__(self):
            return self._langs.__len__()

        def __delitem__(self, key):
            return self._langs.__delitem__(key)

        def __setitem__(self, key, value):
            if key not in self.codes:
                raise AttributeError
            return self._langs.__setitem__(key, value)

        def __getitem__(self, key):
            if key not in self.codes:
                raise KeyError
            return self._langs.__getitem__(key)

    class Children(MutableSequence):
        def __init__(self, node):
            self._node = node
            # TODO: remove and index list ops are O(n). Replace with custom O(1) MutableSequence?
            self._children = []

        @property
        def node(self):
            return self._node

        def __getitem__(self, index):
            return self._children.__getitem__(index)

        def __len__(self):
            return self._children.__len__()

        def insert(self, index, value):
            if not isinstance(value, AstNode):
                raise ValueError
            self._children.append(value)
            value.parent = self._node

        def __delitem__(self, index):
            try:
                child = self._children.pop(index)
                child.parent = None
            except ValueError:
                pass

        def __setitem__(self, index, value):
            if index in self._children:
                self._children[index].parent = None
            self._children[index] = value
            value.parent = self._node

    def __init__(
            self,
            props=None,
            children=None,
            description=None,
            extra_options: Optional[str] = None,
            parent=None,
            uid=None
    ):
        if props:
            assert isinstance(props, MutableMapping)
        self._props = props or {}
        self._description = description or self.Description()
        self._extra_options = "" if extra_options is None else extra_options
        self.uid = uid or uuid4()
        self._children = AstNode.Children(self)

        self._parent = None
        if parent:
            # trigger setter
            self.parent = parent

        if children:
            self._children.extend(children)

    # @property
    # def neighbors(self):
    #     return iter(self._neighbors)
    #
    # @property
    # def incoming(self):
    #     return self._incoming
    #
    # @property
    # def outgoing(self):
    #     return self._outgoing

    # checks structural equality of two nodes
    def compare(self, other):
        if not isinstance(other, type(self)):
            return False

        if len(self.children) != len(other.children):
            return False

        if set(self.props.keys()) ^ set(other.props.keys()):
            return False

        for k in self.props.keys():
            if self.props[k] != other.props[k]:
                return False

        return all(c.compare(other.children[i]) for i, c in enumerate(self.children))

    @property
    def props(self):
        return self._props

    @property
    def children(self):
        return self._children

    @property
    def description(self):
        return self._description

    @property
    def extra_options(self) -> str:
        return self._extra_options

    @extra_options.setter
    def extra_options(self, value: str) -> None:
        self._extra_options = value

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, value):
        assert isinstance(value, AstNode) or value is None

        if value is self._parent:
            return
        if self._parent is not None:
            self._parent.children.remove(self)
        if value is not None and self not in value.children:
            value.children.append(self)

        self._parent = value


class FlagConstant(AstNode):
    def __init__(self, name, value, description=None, extra_options=None, parent=None, uid=None):
        super().__init__(
            props={"name": name, "value": value},
            children=None,
            description=description,
            extra_options=extra_options,
            parent=parent,
            uid=uid
        )

    @property
    def name(self):
        return self._props["name"]

    @name.setter
    def name(self, value):
        self._props["name"] = value

    @property
    def value(self):
        return self._props["value"]

    @value.setter
    def value(self, value):
        self._props["value"] = value

    # def __repr__(self):
    #     return "{} = {:02X}".format(self.name, self.value)


class Argument(AstNode):
    def __init__(self, type_, name, description=None, consts=None, extra_options=None, parent=None,
                 uid=None):
        super().__init__(
            props={"type": type_, "name": name},
            children=consts,
            description=description,
            extra_options=extra_options,
            parent=parent,
            uid=uid
        )

    @property
    def type_(self):
        return self._props["type"]

    @type_.setter
    def type_(self, value):
        self._props["type"] = value

    @property
    def name(self):
        return self._props["name"]

    @name.setter
    def name(self, value):
        self._props["name"] = value

    @property
    def consts(self):
        return self.children

    @consts.setter
    def consts(self, value):
        self.children.clear()
        self.children.extend(value)


class Message(AstNode):
    def __init__(self, args=None, description=None, extra_options=None, parent=None, uid=None):
        super().__init__(
            props=None,
            children=args,
            description=description,
            extra_options=extra_options,
            parent=parent,
            uid=uid
        )

    @property
    def args(self):
        return self.children

    @args.setter
    def args(self, value):
        self.children.clear()
        self.children.extend(value)


class Command(AstNode):
    class Properties(MutableMapping):
        def __init__(self):
            self._data = {}

        def __iter__(self):
            return self._data.__iter__()

        def __setitem__(self, key, value):
            if key == "cid" and not re.match(r"^[a-zA-Z][a-zA-Z0-9]{3}$", value):
                raise ValueError("CID must be exactly 4 symbols string")
            return self._data.__setitem__(key, value)

        def __delitem__(self, key):
            return self._data.__delitem__(key)

        def __len__(self):
            return self._data.__len__()

        def __getitem__(self, key):
            return self._data.__getitem__(key)

    def __init__(
            self,
            cid, name,
            request=None, response=None, description=None, extra_options=None,
            parent=None, uid=None
    ):
        props = Command.Properties()
        props["cid"] = cid
        props["name"] = name

        super().__init__(
            props=props,
            children=[request or Message(), response or Message()],
            description=description,
            extra_options=extra_options,
            parent=parent,
            uid=uid
        )

    @property
    def cid(self):
        return self._props["cid"]

    @cid.setter
    def cid(self, value):
        self._props["cid"] = value

    @property
    def name(self):
        return self._props["name"]

    @name.setter
    def name(self, value):
        self._props["name"] = value

    @property
    def request(self):
        return self.children[0]

    @request.setter
    def request(self, value):
        self.children[0] = value

    @property
    def response(self):
        return self.children[1]

    @response.setter
    def response(self, value):
        self.children[1] = value

    # def __repr__(self):
    #     return "{}: {} ({} -> {})".format(self.cid, self.name, self.request, self.response)


class Protocol(AstNode):
    def __init__(self,
                 name,
                 version,
                 product_name="",
                 device_name="",
                 pid="",
                 vid="",
                 manufacturer="",
                 commands=None,
                 extra_options=None,
                 uid=None):
        super().__init__(
            props={"name": name,
                   "version": version,
                   "product_name": product_name,
                   "device_name": device_name,
                   "pid": pid,
                   "vid": vid,
                   "manufacturer": manufacturer},
            children=commands,
            description=None,
            extra_options=extra_options,
            parent=None,
            uid=uid
        )

    @property
    def name(self):
        return self._props["name"]

    @name.setter
    def name(self, value):
        self._props["name"] = value

    @property
    def version(self):
        return self._props["version"]

    @version.setter
    def version(self, value):
        self._props["version"] = value

    @property
    def product_name(self):
        return self._props["product_name"]

    @product_name.setter
    def product_name(self, value):
        self._props["product_name"] = value

    @property
    def device_name(self):
        return self._props["device_name"]

    @device_name.setter
    def device_name(self, value):
        self._props["device_name"] = value

    @property
    def pid(self):
        return self._props["pid"]

    @pid.setter
    def pid(self, value):
        self._props["pid"] = value

    @property
    def vid(self):
        return self._props["vid"]

    @vid.setter
    def vid(self, value):
        self._props["vid"] = value

    @property
    def manufacturer(self):
        return self._props["manufacturer"]

    @manufacturer.setter
    def manufacturer(self, value):
        self._props["manufacturer"] = value

    @property
    def commands(self):
        return self.children

    @commands.setter
    def commands(self, value):
        self.children.clear()
        self.children.extend(value)
