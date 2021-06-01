from enum import Enum
from itertools import chain
from typing import Optional
from uuid import uuid4, UUID
from weakref import WeakKeyDictionary
from version import BUILDER_VERSION
from bidict import bidict
from tornado.httputil import url_concat
from tornado.web import HTTPError

from frontend.handler.base import BaseRequestHandler
from frontend.util.validator import check_if_empty, check_if_number
from urpc import ast
from urpc.util.accessor import split_by_type
from urpc.util.cconv import cstr_to_type


class AccessorProtocol:
    def __init__(self, protocol):
        self.wrapped = protocol
        commands, accessors = split_by_type(protocol.commands)
        accessors = [
            Accessor(
                aid=acc[0].cid[1:],
                name=acc[0].name[4:],
                extra_options=acc[0].extra_options,
                getter=acc[0],
                setter=acc[1],
                uid=uuid4()
            )
            for acc in accessors
        ]

        self.children = list(chain(commands, accessors))
        # Editor exposes only accessors and their messages, not actual commands

    @property
    def accessors(self):
        return (c for c in self.children if isinstance(c, Accessor))

    @property
    def commands(self):
        return (c for c in self.children if isinstance(c, ast.Command))

    @property
    def version(self):
        return self.wrapped.version

    @version.setter
    def version(self, new_version):
        self.wrapped.version = new_version

    @property
    def name(self):
        return self.wrapped.name

    @name.setter
    def name(self, value):
        self.wrapped.name = value

    @property
    def extra_options(self):
        return self.wrapped.extra_options

    @extra_options.setter
    def extra_options(self, value):
        self.wrapped.extra_options = value

    @property
    def uid(self):
        return self.wrapped.uid


class Accessor:
    def __init__(self, aid, name, extra_options, getter, setter, uid):
        self._aid = None
        self._extra_options = None
        # Trigger setter
        self.aid = aid
        self.name = name
        self.extra_options = extra_options
        self.getter = getter
        self.setter = setter
        self.uid = uid

    @property
    def aid(self):
        return self._aid

    @aid.setter
    def aid(self, value):
        if not isinstance(value, str) or len(value) != 3:
            raise ValueError("AID must be exactly 3 bytes string")
        self._aid = value

    @property
    def children(self):
        return (self.getter, self.setter)

    @property
    def description(self):
        return self.getter.description

    @property
    def extra_options(self):
        return self._extra_options

    @extra_options.setter
    def extra_options(self, value):
        self._extra_options = value


class ResourceKind(Enum):
    protocol = AccessorProtocol
    accessor = Accessor
    command = ast.Command
    message = ast.Message
    argument = ast.Argument
    constant = ast.FlagConstant


class EditorSession:
    def __init__(self, protocol):
        self._draft = AccessorProtocol(protocol)
        self._handles = bidict()
        # keys: children nodes, values: parent nodes
        self._parent_links = {}

        self._add_children_handles(self._draft)

    @property
    def protocol(self):
        return self._draft

    def breadcrumbs_by_handle(self, handle, handler):
        breadcrumb = []
        kind = self.get_kind_by_handle(handle)
        if kind is ResourceKind.command:
            cmd = self._handles[handle]
            breadcrumb.append({"name": cmd.name,
                               "value": url_concat(handler.reverse_url("editor")[1:],
                                                   {"action": "view", "handle": handle})})
        elif kind is ResourceKind.accessor:
            acc = self._handles[handle]
            breadcrumb.append({"name": acc.name,
                               "value": url_concat(handler.reverse_url("editor")[1:],
                                                   {"action": "view", "handle": handle})})
        elif kind is ResourceKind.argument:
            arg = self._handles[handle]
            msg = self._parent_links[arg]
            cmd = self._parent_links[msg]

            assert isinstance(arg, ast.Argument) and isinstance(msg, ast.Message) and isinstance(cmd, ast.Command)
            parent = self._parent_links[cmd]
            if isinstance(parent, AccessorProtocol):
                parent = cmd
            breadcrumb.append({"name": parent.name,
                               "value": url_concat(handler.reverse_url("editor")[1:],
                                                   {"action": "view", "handle": parent.uid})})
            breadcrumb.append({"name": arg.name,
                               "value": url_concat(handler.reverse_url("editor")[1:],
                                                   {"action": "view", "handle": handle})})
        elif kind is ResourceKind.constant:
            con = self._handles[handle]
            arg = self._parent_links[con]
            msg = self._parent_links[arg]
            cmd = self._parent_links[msg]

            assert isinstance(arg, ast.Argument) and isinstance(msg, ast.Message) and isinstance(cmd, ast.Command)
            parent = self._parent_links[cmd]
            if isinstance(parent, AccessorProtocol):
                parent = cmd
            breadcrumb.append({"name": parent.name,
                               "value": url_concat(handler.reverse_url("editor")[1:],
                                                   {"action": "view", "handle": parent.uid})})
            breadcrumb.append({"name": arg.name,
                               "value": url_concat(handler.reverse_url("editor")[1:],
                                                   {"action": "view", "handle": arg.uid})})
            breadcrumb.append({"name": con.name,
                               "value": url_concat(handler.reverse_url("editor")[1:],
                                                   {"action": "view", "handle": handle})})
        return breadcrumb

    def get_kind_by_handle(self, handle):
        if handle not in self._handles:
            raise ValueError

        resource = self._handles[handle]
        kind = next((m for m in ResourceKind if isinstance(resource, m.value)), None)

        assert kind is not None
        return kind

    def if_request_by_handle(self, handle):
        msg = self._handles[handle]
        cmd = self._parent_links[msg]
        assert isinstance(cmd, ast.Command)
        if cmd.request == msg:
            return True
        return False

    def cmd_by_message(self, handle):
        msg = self._handles[handle]
        cmd = self._parent_links[msg]
        assert isinstance(cmd, ast.Command)
        return cmd.uid

    def get_prev_id(self, handle, default_val=""):
        kind = self.get_kind_by_handle(handle)
        elem = self._handles[handle]
        parent = self._parent_links[elem]

        elements = list(parent.children)

        if kind is ResourceKind.accessor:
            elements = list(filter(lambda elem: isinstance(elem, Accessor), parent.children))

        prev_command_index = elements.index(elem) - 1
        if prev_command_index < 0:
            if kind is ResourceKind.argument:
                msg = parent
                cmd = self._parent_links[msg]
                pr = self._parent_links[cmd]
                if isinstance(pr, AccessorProtocol):
                    if not self.if_request_by_handle(msg.uid):
                        return default_val
            if kind is ResourceKind.accessor:
                return default_val
            return ""
        return str(elements[prev_command_index].uid)

    def _add_children_handles(self, node, parent=None):
        self._handles[node.uid] = node
        self._parent_links[node] = parent
        for c in node.children:
            self._add_children_handles(c, node)

    def _purge_children_handles(self, node):
        del self._handles.inv[node]
        del self._parent_links[node]
        for c in node.children:
            self._purge_children_handles(c)

    def update_protocol(self, handle, project_name=None, version=None, extra_options: Optional[str] = None):
        assert self._draft

        protocol = self._handles[handle]

        assert isinstance(protocol, AccessorProtocol)

        if project_name is not None:
            protocol.name = project_name
        if version is not None:
            protocol.version = version
        if extra_options is not None:
            protocol.extra_options = extra_options

        return protocol.uid

    def update_command(self, handle, cid=None, name=None, descrs=None, extra_options: Optional[str] = None):
        assert self._draft

        cmd = self._handles[handle]

        assert isinstance(cmd, ast.Command)

        cmd.cid = cid
        cmd.name = name

        for code, text in descrs.items():
            cmd.description[code] = text

        cmd.extra_options = extra_options

        return cmd.uid

    def update_accessor(self, handle=None, aid=None, name=None, descrs=None, extra_options: Optional[str] = None):
        assert self._draft

        acc = self._handles[handle]

        assert isinstance(acc, Accessor)

        acc.aid = aid
        acc.getter.cid = "g" + aid
        acc.setter.cid = "s" + aid

        acc.name = name
        acc.getter.name = "get_" + name
        acc.setter.name = "set_" + name

        acc.extra_options = extra_options
        acc.getter.extra_options = extra_options
        acc.setter.extra_options = extra_options

        for code, text in descrs.items():
            acc.setter.description[code] = text
            acc.getter.description[code] = text

    def update_argument(self, handle, _type=None, name=None, descrs=None, extra_options: Optional[str] = None):
        def upd_arg(a):
            a.type_ = _type
            a.name = name
            for code, text in descrs.items():
                a.description[code] = text

            a.extra_options = extra_options

        arg = self._handles[handle]
        msg = self._parent_links[arg]
        cmd = self._parent_links[msg]

        assert isinstance(arg, ast.Argument) and isinstance(msg, ast.Message) and isinstance(cmd, ast.Command)

        parent = self._parent_links[cmd]
        if not isinstance(parent, AccessorProtocol):
            acc = parent
            assert isinstance(acc, Accessor)

            arg2 = None
            if cmd == acc.getter:
                arg2 = acc.setter.request.args[msg.args.index(arg)]
            else:
                arg2 = acc.getter.response.args[msg.args.index(arg)]
            upd_arg(arg2)

        upd_arg(arg)

        return arg.uid

    def update_constant(self, handle, name, val, descrs=None, extra_options: Optional[str] = None):

        def upd_con(con):
            con.name = name
            con.value = int(val)
            con.extra_options = extra_options
            for code, text in descrs.items():
                con.description[code] = text

        const = self._handles[handle]

        arg = self._parent_links[const]
        msg = self._parent_links[arg]
        cmd = self._parent_links[msg]

        assert isinstance(arg, ast.Argument) and isinstance(msg, ast.Message) and isinstance(cmd, ast.Command)

        parent = self._parent_links[cmd]
        if not isinstance(parent, AccessorProtocol):
            acc = parent
            assert isinstance(acc, Accessor)

            const2 = None
            if cmd == acc.getter:
                const2 = acc.setter.request.args[msg.args.index(arg)].consts[arg.consts.index(const)]
            else:
                const2 = acc.getter.response.args[msg.args.index(arg)].consts[arg.consts.index(const)]
            upd_con(const2)

        upd_con(const)

    def create_protocol(self, parent_handle, name, version, project_name):
        raise NotImplementedError

    def create_command(self, parent_handle, cid, name):
        assert self._draft

        protocol = self._handles[parent_handle]

        assert isinstance(protocol, AccessorProtocol)

        cmd = ast.Command(cid=cid, name=name)

        protocol.children.append(cmd)
        protocol.wrapped.commands.append(cmd)

        self._add_children_handles(cmd, protocol)

        return cmd.uid

    def create_accessor(self, parent_handle, aid, name, extra=None):
        assert self._draft
        protocol = self._handles[parent_handle]

        assert isinstance(protocol, AccessorProtocol)

        try:
            getter = ast.Command(cid="g" + aid, name="get_" + name)
            setter = ast.Command(cid="s" + aid, name="set_" + name)
        except ValueError:
            raise ValueError("AID must be exactly 3 bytes string")

        protocol.wrapped.commands.append(getter)
        protocol.wrapped.commands.append(setter)
        acc = Accessor(aid=aid, name=name, getter=getter, setter=setter, uid=uuid4(), extra_options=extra)

        protocol.children.append(acc)
        self._add_children_handles(acc, protocol)

        return acc.uid

    def create_argument(self, handle, name, _type):
        assert self._draft
        obj = self._handles[handle]
        if isinstance(obj, Accessor):
            arg1, arg2 = (ast.Argument(type_=_type, name=name), ast.Argument(type_=_type, name=name))
            obj.getter.response.args.append(arg1)
            obj.setter.request.args.append(arg2)
            self._add_children_handles(arg1, obj.getter.response)
            self._add_children_handles(arg2, obj.setter.request)
            return arg1.uid

        msg = obj
        assert isinstance(msg, ast.Message)

        arg = ast.Argument(type_=_type, name=name)
        msg.args.append(arg)
        self._add_children_handles(arg, msg)

        return self._parent_links[arg]

    def create_constant(self, handle, name, value):
        assert self._draft

        arg = self._handles[handle]
        msg = self._parent_links[arg]
        cmd = self._parent_links[msg]

        assert isinstance(arg, ast.Argument) and isinstance(msg, ast.Message) and isinstance(cmd, ast.Command)

        parent = self._parent_links[cmd]
        if not isinstance(parent, AccessorProtocol):
            const2 = ast.FlagConstant(name, value)
            acc = parent
            assert isinstance(acc, Accessor)
            arg2 = None
            if cmd == acc.getter:
                arg2 = acc.setter.request.args[msg.args.index(arg)]
            else:
                arg2 = acc.getter.response.args[msg.args.index(arg)]
            arg2.consts.append(const2)
            self._add_children_handles(const2, arg2)

        const = ast.FlagConstant(name, value)
        arg.consts.append(const)

        self._add_children_handles(const, arg)

        return self._parent_links[const]

    def delete_protocol(self, handle):
        raise NotImplementedError

    def delete_command(self, handle):
        assert self._draft

        cmd = self._handles[handle]
        protocol = self._parent_links[cmd]

        assert isinstance(cmd, ast.Command)

        self._purge_children_handles(cmd)
        protocol.children.remove(cmd)
        protocol.wrapped.children.remove(cmd)

        return protocol.uid

    def delete_accessor(self, handle):
        assert self._draft

        acc = self._handles[handle]
        protocol = self._parent_links[acc]

        assert isinstance(acc, Accessor)

        protocol.children.remove(acc)

        self._purge_children_handles(acc)
        protocol.wrapped.children.remove(acc.getter)
        protocol.wrapped.children.remove(acc.setter)

        return protocol.uid

    def delete_argument(self, handle):
        assert self._draft

        arg = self._handles[handle]
        msg = self._parent_links[arg]
        cmd = self._parent_links[msg]

        assert isinstance(arg, ast.Argument) and isinstance(msg, ast.Message) and isinstance(cmd, ast.Command)

        parent = self._parent_links[cmd]
        acc = None
        if not isinstance(parent, AccessorProtocol):
            acc = parent
            assert isinstance(acc, Accessor)

            arg2 = None
            if cmd == acc.getter:
                arg2 = acc.setter.request.args[msg.args.index(arg)]
            else:
                arg2 = acc.getter.response.args[msg.args.index(arg)]
            msg2 = self._parent_links[arg2]
            assert isinstance(msg2, ast.Message)

            self._purge_children_handles(arg2)
            msg2.children.remove(arg2)

        self._purge_children_handles(arg)
        msg.children.remove(arg)

        result = acc if acc else cmd
        return result.uid

    def delete_constant(self, handle):
        assert self._draft

        const = self._handles[handle]
        assert isinstance(const, ast.FlagConstant)

        arg = self._parent_links[const]
        msg = self._parent_links[arg]
        cmd = self._parent_links[msg]

        assert isinstance(arg, ast.Argument) and isinstance(msg, ast.Message) and isinstance(cmd, ast.Command)

        parent = self._parent_links[cmd]
        if not isinstance(parent, AccessorProtocol):
            acc = parent
            assert isinstance(acc, Accessor)

            const2 = None
            if cmd == acc.getter:
                const2, arg2 = (acc.setter.request.args[msg.args.index(arg)].consts[arg.consts.index(const)],
                                acc.setter.request.args[msg.args.index(arg)])
            else:
                const2, arg2 = (acc.getter.response.args[msg.args.index(arg)].consts[arg.consts.index(const)],
                                acc.getter.response.args[msg.args.index(arg)])
            self._purge_children_handles(const2)
            arg2.children.remove(const2)

        self._purge_children_handles(const)
        arg.children.remove(const)

        return arg.uid

    def move_argument(self, handle, offset):
        assert self._draft

        arg = self._handles[handle]
        msg = self._parent_links[arg]
        cmd = self._parent_links[msg]

        assert isinstance(arg, ast.Argument) and isinstance(msg, ast.Message) and isinstance(cmd, ast.Command)

        current_index = msg.args.index(arg)
        new_index = current_index + offset
        if_move = (new_index >= 0 and new_index < len(msg.args))

        parent = self._parent_links[cmd]
        acc = None
        if not isinstance(parent, AccessorProtocol):
            acc = parent
            assert isinstance(acc, Accessor)

            msg2 = None
            if cmd == acc.getter:
                msg2 = acc.setter.request
            else:
                msg2 = acc.getter.response
            if if_move:
                msg2.args[current_index], msg2.args[new_index] = msg2.args[new_index], msg2.args[current_index]

        if if_move:
            msg.args[current_index], msg.args[new_index] = msg.args[new_index], msg.args[current_index]

        result = acc if acc else cmd
        return result.uid

    def read_protocol(self, handle):
        assert self._draft

        protocol = self._handles[handle]

        assert isinstance(protocol, AccessorProtocol)

        return protocol

    def read_command(self, handle):
        assert self._draft

        cmd = self._handles[handle]
        assert isinstance(cmd, ast.Command)

        return cmd

    def read_accessor(self, handle):
        assert self._draft

        acc = self._handles[handle]
        assert isinstance(acc, Accessor)

        return acc

    def read_argument(self, handle):
        assert self._draft

        argument = self._handles[handle]
        assert isinstance(argument, ast.Argument)

        return argument

    def read_constant(self, handle=None):
        assert self._draft

        constant = self._handles[handle]
        assert isinstance(constant, ast.FlagConstant)

        return constant


class EditorHandler(BaseRequestHandler):
    # may create bugs in multithreaded code but should be completely fine when used singlethreaded
    # editor is cleared from memory when SessionManager dumps protocol from RAM cache to disk
    _cached_editors = WeakKeyDictionary()
    messages = {}

    def __init__(self, application, request, sessions, **kwargs):
        super().__init__(application, request, **kwargs)

        protocol = sessions[self.current_user]
        self.breadcrumbs = []

        # WeakValues" setdefault() method apparently has some kind of bug
        if protocol in self._cached_editors:
            self._editor = self._cached_editors[protocol]
        else:
            self._editor = EditorSession(protocol)
            self._cached_editors[protocol] = self._editor

    def get(self):
        action = self.get_query_argument("action")
        handle, kind = None, None
        try:
            handle = UUID(self.get_query_argument("handle"))
            kind = self._editor.get_kind_by_handle(handle)
        except ValueError:
            self.redirect("main")

        if action == "view":
            if kind is ResourceKind.protocol:
                self.render("editor/protocol.html", protocol=self._editor.read_protocol(handle),
                            messages=EditorHandler.messages,
                            breadcrumbs=[], version=BUILDER_VERSION)
            elif kind is ResourceKind.command:
                self.render("editor/command.html", command=self._editor.read_command(handle),
                            messages=EditorHandler.messages,
                            breadcrumbs=self._editor.breadcrumbs_by_handle(handle, self), version=BUILDER_VERSION)
            elif kind is ResourceKind.accessor:
                self.render("editor/accessor.html", accessor=self._editor.read_accessor(handle),
                            messages=EditorHandler.messages,
                            breadcrumbs=self._editor.breadcrumbs_by_handle(handle, self), version=BUILDER_VERSION)
            elif kind is ResourceKind.argument:
                self.render("editor/argument.html", argument=self._editor.read_argument(handle),
                            messages=EditorHandler.messages,
                            breadcrumbs=self._editor.breadcrumbs_by_handle(handle, self), version=BUILDER_VERSION)
            elif kind is ResourceKind.constant:
                self.render("editor/constant.html", constant=self._editor.read_constant(handle),
                            messages=EditorHandler.messages,
                            breadcrumbs=self._editor.breadcrumbs_by_handle(handle, self), version=BUILDER_VERSION)
        else:
            raise HTTPError(404)
        EditorHandler.messages = {}

    def _protocol_post(self, action, handle):
        if action == "update":
            project_name = self.get_body_argument("project_name", None)
            version = self.get_body_argument("version")
            extra_options = self.get_body_argument("extra_options", "")
            self._editor.update_protocol(
                handle=handle,
                project_name=project_name,
                version=version,
                extra_options=extra_options
            )
            self.redirect(url_concat(self.reverse_url("editor")[1:], {"action": "view", "handle": handle}))
        elif action == "create_command":
            cid, name = self.get_body_argument("cid"), self.get_body_argument("command_name")
            try:
                check_if_empty(name, "Name")
                self._editor.create_command(handle, cid, name)
            except ValueError as e:
                EditorHandler.messages["command-message"] = str(e)
            self.redirect(url_concat(self.reverse_url("editor")[1:], {"action": "view", "handle": handle}))
        elif action == "create_accessor":
            aid = self.get_body_argument("aid")
            name = self.get_body_argument("accessor_name")
            try:
                check_if_empty(name, "Name")
                self._editor.create_accessor(handle, aid, name)
            except ValueError as e:
                EditorHandler.messages["accessor-message"] = str(e)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": handle}) + "#___accessor")

    def _accessor_post(self, action, handle):
        if action == "delete":
            postfix_hook = "#" + self._editor.get_prev_id(handle, "___accessor")
            protocol_handle = self._editor.delete_accessor(handle)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": protocol_handle}) + postfix_hook)
        elif action == "update":
            aid = self.get_body_argument("aid", None)
            name = self.get_body_argument("accessor_name", None)
            descrs = {c: self.get_body_argument(c + "_description", "") for c in ast.AstNode.Description.codes}
            extra_options = self.get_body_argument("extra_options", "")
            try:
                check_if_empty(name, "Name")
                self._editor.update_accessor(
                    handle=handle,
                    aid=aid,
                    name=name,
                    descrs=descrs,
                    extra_options=extra_options
                )
            except ValueError as e:
                EditorHandler.messages["accessor-message"] = str(e)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": handle}) + "#___accessor")
        if action == "create_argument":
            name, type_length = self.get_body_argument("name"), self.get_body_argument("type_length", 0)
            try:
                check_if_empty(name, "Name"), check_if_number(type_length, "Array length")
                type_obj = cstr_to_type(self.get_body_argument("value_type"), type_length)
                self._editor.create_argument(handle, name, type_obj)
            except ValueError as e:
                EditorHandler.messages["argument-message"] = str(e)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": handle}) + "#___accessor")

    def _command_post(self, action, handle):
        if action == "delete":
            # res = self._editor.get_prev_id(handle)
            postfix_hook = "#" + self._editor.get_prev_id(handle)
            protocol_handle = self._editor.delete_command(handle)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": protocol_handle}) + postfix_hook)
        elif action == "update":
            cid = self.get_body_argument("cid", None)
            name = self.get_body_argument("command_name", None)
            descrs = {c: self.get_body_argument(c + "_description", "") for c in ast.AstNode.Description.codes}
            extra_options = self.get_body_argument("extra_options", None)
            try:
                check_if_empty(name, "Name")
                self._editor.update_command(
                    handle=handle,
                    cid=cid,
                    name=name,
                    descrs=descrs,
                    extra_options=extra_options
                )
            except ValueError as e:
                EditorHandler.messages["command-message"] = str(e)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": handle}) + "#___command")

    def _message_post(self, action, handle):
        if action == "create_argument":
            name, type_length = self.get_body_argument("name"), self.get_body_argument("type_length", 0)
            try:
                check_if_empty(name, "Name"), check_if_number(type_length, "Array length")
                type_obj = cstr_to_type(self.get_body_argument("value_type"), type_length)
                self._editor.create_argument(handle, name, type_obj)
            except ValueError as e:
                if self._editor.if_request_by_handle(handle):
                    EditorHandler.messages["command-request-message"] = str(e)
                else:
                    EditorHandler.messages["command-response-message"] = str(e)
            postfix_hook = "#___command"
            if not self._editor.if_request_by_handle(handle):
                postfix_hook = "#___response"
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view",
                                      "handle": self._editor.cmd_by_message(handle)}) + postfix_hook)

    def _argument_post(self, action, handle):
        if action == "delete":
            postfix_hook = "#" + self._editor.get_prev_id(handle, "___response")
            parent_handle = self._editor.delete_argument(handle)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": parent_handle}) + postfix_hook)
        elif action == "update":
            name, type_length = self.get_body_argument("name"), self.get_body_argument("type_length", 0)
            try:
                check_if_empty(name, "Name"), check_if_number(type_length, "Array length")
                type_obj = cstr_to_type(self.get_body_argument("value_type"), type_length)
                descrs = {c: self.get_body_argument(c + "_description", "") for c in ast.AstNode.Description.codes}
                extra_options = self.get_body_argument("extra_options", None)
                self._editor.update_argument(
                    handle=handle,
                    _type=type_obj,
                    name=name,
                    descrs=descrs,
                    extra_options=extra_options
                )
            except ValueError as e:
                EditorHandler.messages["argument-message"] = str(e)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": handle}) + "#___argument")
        elif action == "create_constant":
            name = self.get_body_argument("name")
            value = self.get_body_argument("value")
            try:
                check_if_empty(name, "Name"), check_if_empty(value), check_if_number(value)
                value = int(value)
                self._editor.create_constant(handle, name, value)
            except ValueError as e:
                EditorHandler.messages["constant-message"] = str(e)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": handle}) + "#___argument")
        elif action == "raise":
            postfix_hook = "#" + self._editor.get_prev_id(handle, "___response")
            parent_handle = self._editor.move_argument(handle, -1)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": parent_handle}) + postfix_hook)
        elif action == "lower":
            postfix_hook = "#" + self._editor.get_prev_id(handle, "___response")
            parent_handle = self._editor.move_argument(handle, 1)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": parent_handle}) + postfix_hook)

    def _constant_post(self, action, handle):
        if action == "delete":
            postfix_hook = "#" + self._editor.get_prev_id(handle)
            parent_handle = self._editor.delete_constant(handle)
            self.redirect(url_concat(self.reverse_url("editor")[1:],
                                     {"action": "view", "handle": parent_handle}) + postfix_hook)
        elif action == "update":
            name = self.get_body_argument("name", None)
            value = self.get_body_argument("value")
            descrs = {c: self.get_body_argument(c + "_description", "") for c in ast.AstNode.Description.codes}
            extra_options = self.get_body_argument("extra_options", "")
            try:
                check_if_empty(name, "Name"), check_if_empty(value), check_if_number(value)
                value = int(value)
                self._editor.update_constant(
                    handle=handle,
                    name=name,
                    val=value,
                    descrs=descrs,
                    extra_options=extra_options
                )
            except ValueError as e:
                EditorHandler.messages["constant-message"] = str(e)
            self.redirect(url_concat(self.reverse_url("editor")[1:], {"action": "view", "handle": handle}))

    def post(self):
        action = self.get_body_argument("action")
        handle, kind = None, None
        try:
            handle = UUID(self.get_body_argument("handle"))
            kind = self._editor.get_kind_by_handle(handle)
        except ValueError:
            self.redirect(self.reverse_url("main"))

        if kind is ResourceKind.protocol:
            self._protocol_post(action, handle)
        elif kind is ResourceKind.accessor:
            self._accessor_post(action, handle)
        elif kind is ResourceKind.command:
            self._command_post(action, handle)
        elif kind is ResourceKind.message:
            self._message_post(action, handle)
        elif kind is ResourceKind.argument:
            self._argument_post(action, handle)
        elif kind is ResourceKind.constant:
            self._constant_post(action, handle)
