from itertools import chain
from os.path import abspath, join, dirname, relpath
from zipfile import ZipFile, ZIP_DEFLATED

import mako.exceptions
import mako.lookup

from urpc import ast
from urpc.builder.util import ClangView
from urpc.builder.util.resource import resources

__all__ = ["build", "get_extra_option", "get_bool", "get_int", "get_number", "get_str"]

_module_path = abspath(dirname(__file__))
_lookup = mako.lookup.TemplateLookup((join(_module_path, "resources"),), input_encoding="utf-8",
                                     output_encoding="utf-8")

_tango_types = (
    "DevBoolean",
    "DevShort",
    "DevBoolean",
    "DevShort",
    "DevLong",
    "DevLong64 ",
    "DevFloat",
    "DevDouble",
    "DevUShort ",
    "DevULong ",
    "DevULong64",
    "DevString",
    "DevVarCharArray",
    "DevVarShortArray",
    "DevVarLongArray",
    "DevVarLong64Array",
    "DevVarFloatArray",
    "DevVarDoubleArray",
    "DevVarUShortArray",
    "DevVarULongArray",
    "DevVarULong64Array",
    "DevVarStringArray",
    "DevVarLongStringArray",
    "DevVarDoubleStringArray",
    "DevState",
    "DevEncode",
)


# Buffer = namedtuple("Buffer", ("name", "type"))
# Member = namedtuple("Member", ("name", "buffer_field"))
#
#
# class Group:
#     @property
#     def buffers(self):
#         raise NotImplementedError()
#
#
# class ReadModifyWriteGroup(Group):
#     def __init__(self, acc, argstructs):
#         self._getter, self._setter = acc
#         self._argstructs = argstructs
#
#         # TODO: replace with actual accessor name once it available
#         self.name = self._getter.name[3:]
#
#         buffer_name = "{}_buffer".format(self.name)
#         buffer_type = argstructs[self._getter.response]
#         self.buffer = Buffer(buffer_name, buffer_type)
#
#     @property
#     def buffers(self):
#         yield self.buffer
#
#     @property
#     def setter_func(self):
#         return self._getter.name
#
#     @property
#     def getter_func(self):
#         return self._getter.name
#
#     @property
#     def attributes(self):
#         for attr in self._getter.response.children:
#             yield Member("{}_{}".format(self.name, attr.name), attr.name)
#
#
# class ReadThroughGroup(Group):
#     def __init__(self, cmd, argstructs):
#         assert len(cmd.response.children) != 0
#         self._cmd = cmd
#
#         buffer_name = "{}_buffer".format(self._cmd.name)
#         buffer_type = argstructs[self._cmd.response]
#         self.buffer = Buffer(buffer_name, buffer_type)
#
#     @property
#     def func_name(self):
#         return self._cmd.name
#
#     @property
#     def buffers(self):
#         yield self.buffer
#
#     @property
#     def attributes(self):
#         for attr in self._cmd.response.children:
#             yield Member("{}_{}".format(self._cmd.name, attr.name), attr.name)
#
#
# class ExplicitSyncGroup(Group):
#     def __init__(self, cmd, argstructs):
#         self._cmd = cmd
#         self._argstructs = argstructs
#         assert len(cmd.request.children) != 0
#
#         self.in_buffer = Buffer("in_{}_buffer".format(self.name), argstructs[cmd.request].name)
#
#         self.out_buffer = None
#         if len(cmd.response.children) != 0:
#             self.out_buffer = Buffer("out_{}_buffer".format(self.name), argstructs[cmd.response].name)
#
#     @property
#     def buffers(self):
#         yield self.in_buffer
#         if not self.out_buffer:
#             return
#         yield self.out_buffer
#
#     @property
#     def name(self):
#         return self._cmd.name
#
#     @property
#     def func_name(self):
#         return self._cmd.name
#
#     def _attrbutes(self, msg):
#         for arg in msg.children:
#             yield Member("{}_{}".format(self.name, arg.name), arg.name)
#
#     @property
#     def write_attributes(self):
#         yield from self._attrbutes(self._cmd.request)
#
#     @property
#     def read_attributes(self):
#         yield from self._attrbutes(self._cmd.response)
#
#     @property
#     def attributes(self):
#         return chain(self.write_attributes, self.read_attributes)
#
#
# class CommandGroup:
#     def __init__(self, cmd, argstructs):
#         self._cmd = cmd
#
#         self.in_buffer = None
#         if len(cmd.request.children):
#             self.in_buffer = Buffer("in_{}_buffer".format(self.name), argstructs[cmd.request].name)
#
#         self.out_buffer = None
#         if len(cmd.response.children) != 0:
#             self.out_buffer = Buffer("out_{}_buffer".format(self.name), argstructs[cmd.response].name)
#
#     @property
#     def buffers(self):
#         for b in (self.in_buffer, self.out_buffer):
#             if b is None:
#                 continue
#             yield b
#
#     @property
#     def name(self):
#         return self._cmd.name
#
#     @property
#     def func_name(self):
#         return self._cmd.name


class TangoView(ClangView):
    def __init__(self, project):
        super().__init__(project)

    # TODO: this should also go away
    def is_accessor_part(self, cmd):
        assert isinstance(cmd, ast.Command) and cmd in self._project.children
        return cmd not in self._commands

    # standalone utility functions
    def argstruct_for_cmd(self, msg):
        assert msg in self._argstructs
        return self._argstructs[msg]

    def is_request(self, msg):
        return msg.parent.request == msg

    def is_response(self, msg):
        return msg.parent.response == msg

    def needs_external_buffer(self, msg):
        return self.has_ext_args(msg)

    def external_args(self, msg):
        yield from msg.args

    def handled_internally(self, msg):
        # return len(msg.args) == 1
        return False

    def has_ext_args(self, msg):
        # return len(msg.args) > 1
        return len(msg.args) > 0

    def protocol_has_reactive_attrs(self, protocol) -> bool:
        return any(
            map(
                self.cmd_has_reactive_attrs,
                chain(self.all_cmds(protocol), map(lambda getter_setter: getter_setter[0], self.all_accs(protocol)))
            )
        )

    def cmd_has_reactive_attrs(self, cmd):
        assert isinstance(cmd, ast.Command)

        default_is_reactive = get_extra_option(cmd.extra_options, "reactive", get_bool())
        return \
            not self.has_ext_args(cmd.request) and self.has_ext_args(cmd.response) \
            and any(
                get_extra_option(arg.extra_options, "reactive", get_bool(default_is_reactive))
                for arg in cmd.response.children
            )

    def cmd_is_reactive(self, cmd):
        assert isinstance(cmd, ast.Command)
        return get_extra_option(cmd.extra_options, "reactive", get_bool(False))

    def cmd_poll_ms(self, cmd):
        assert isinstance(cmd, ast.Command)
        return get_extra_option(cmd.extra_options, "poll_ms", get_int(1000))

    def attr_is_reactive(self, arg):
        assert isinstance(arg, ast.Argument)
        return get_extra_option(
            arg.extra_options,
            "reactive",
            get_bool(get_extra_option(arg.parent.parent.extra_options, "reactive", get_bool()))
        )

    def attr_delta_abs(self, arg):
        assert isinstance(arg, ast.Argument)
        return get_extra_option(arg.extra_options, "delta_abs", get_number())

    def attr_delta_rel(self, arg):
        assert isinstance(arg, ast.Argument)
        return get_extra_option(arg.extra_options, "delta_rel", get_number())

    def attr_get_option_by_name(self, arg, option):
        return get_extra_option(arg.extra_options, option, get_str())

    def get_arg(self, msg):
        assert self.handled_internally(msg)
        return next(iter(msg.args))

    def args_as_attrs(self, msg):
        # if self.handled_internally(msg):
        #     return
        for arg in msg.args:
            yield arg

    def all_args_as_attrs(self, protocol):
        # TODO: replace with actual accessors and commands access on protocol object
        for cmd in self._commands:
            yield from self.args_as_attrs(cmd.request)
            yield from self.args_as_attrs(cmd.response)
        for (getter, setter) in self._accessors:
            yield from getter.response.args

    def all_cmds(self, protocol):
        yield from self._commands

    # TODO: replace with actual accessors and commands iteration on AST when view is implemented
    def all_accs(self, protocol):
        yield from self._accessors

    def device_name(self, protocol) -> str:
        return "{}TDS".format(protocol.name.capitalize())

    def upper_device_name(self, protocol) -> str:
        return "{}TDS".format(protocol.name.upper())

    def server_name(self, protocol) -> str:
        return protocol.name.capitalize()

    def tango_type(self, t):
        pattern = "{}"
        if isinstance(t, ast.ArrayType):
            pattern = "{}*"
            t = t.type_

        if t in (ast.Integer8s, ast.Integer8u):
            return pattern.format("DevUChar")
        elif t == ast.Integer16u:
            return pattern.format("DevUShort")
        elif t == ast.Integer16s:
            return pattern.format("DevShort")
        elif t == ast.Integer32u:
            return pattern.format("DevULong")
        elif t == ast.Integer32s:
            return pattern.format("DevLong")
        elif t == ast.Integer64u:
            return pattern.format("DevULong64")
        elif t == ast.Integer64s:
            return pattern.format("DevLong64")
        elif t == ast.Float:
            return pattern.format("DevFloat")

        assert False, "{} can't be represented with any TANGO type".format(t)


def get_extra_option(extra_options: str, option: str, get):
    for kv in extra_options.split(","):
        kv_list = kv.split("=", 1)
        if len(kv_list) == 2:
            key = kv_list[0].strip()
            if key == option:
                return get(kv_list[1].strip())
        else:
            key = kv_list[0].strip()
            if key == option:
                return get()

    return get()


def get_bool(default=False):
    def do_get(s=None):
        if s is None:
            return default
        elif s.lower() in ("true", "1"):
            return True
        else:
            return False

    return do_get


def get_int(default="0"):
    if not isinstance(default, str):
        default = str(default)

    def do_get(s=None):
        if s is None:
            return default
        else:
            try:
                int(s)
            except Exception:
                return default
            else:
                return s

    return do_get


def get_number(default="0"):
    if not isinstance(default, str):
        default = str(default)

    def do_get(s=None):
        if s is None:
            return default
        else:
            try:
                int(s)
            except Exception:
                try:
                    float(s)
                except Exception:
                    return default
                else:
                    return s
            else:
                return s

    return do_get


def get_str(default=""):
    def do_get(s=None):
        if s is None:
            return default
        else:
            return s

    return do_get


def build(project, output):
    view = TangoView(project)

    utils = {
        "BUILDER_VERSION_MAJOR": view.BUILDER_VERSION_MAJOR,
        "BUILDER_VERSION_MINOR": view.BUILDER_VERSION_MINOR,
        "BUILDER_VERSION_BUGFIX": view.BUILDER_VERSION_BUGFIX,
        "BUILDER_VERSION_SUFFIX": view.BUILDER_VERSION_SUFFIX,
        "BUILDER_VERSION": view.BUILDER_VERSION,

        "handled_internally": view.handled_internally,
        "is_request": view.is_request,
        "is_response": view.is_response,
        "argstruct_for_cmd": view.argstruct_for_cmd,
        "is_accessor_part": view.is_accessor_part,
        "has_ext_args": view.has_ext_args,

        # Extra options parsing
        "cmd_has_reactive_attrs": view.cmd_has_reactive_attrs,
        "protocol_has_reactive_attrs": view.protocol_has_reactive_attrs,

        "cmd_is_reactive": view.cmd_is_reactive,
        "cmd_poll_ms": view.cmd_poll_ms,

        "attr_is_reactive": view.attr_is_reactive,
        "attr_delta_abs": view.attr_delta_abs,
        "attr_delta_rel": view.attr_delta_rel,
        "attr_get_option_by_name": view.attr_get_option_by_name,

        "get_arg": view.get_arg,
        "all_args_as_attrs": view.all_args_as_attrs,
        "all_cmds": view.all_cmds,
        "all_accs": view.all_accs,
        "device_name": view.device_name,
        "upper_device_name": view.upper_device_name,
        "server_name": view.server_name,
        "library_shared_file": view.library_shared_file,
        "library_header_file": view.library_header_file,
        "needs_external_buffer": view.needs_external_buffer,
        "external_args": view.external_args,
        "tango_type": view.tango_type}

    def import_file(filename):
        return filename

    subdir_path = join(_module_path, "resources")
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for file in resources(subdir_path):
            archive_path = file[len(subdir_path) + 1:]
            if file.endswith(".mako"):
                try:
                    rendered_file = _lookup.get_template(archive_path).render_unicode(
                        protocol=project,
                        is_namespaced=True,
                        import_file=import_file,
                        **utils
                    )
                except Exception as e:
                    raise type(e)(
                        'When rendering file "{file}" caught exception. Details:'
                        "{cause_traceback}".format(
                            file=relpath(file, subdir_path),
                            cause_traceback=mako.exceptions.text_error_template().render(
                                protocol=project,
                                is_namespaced=True,
                                **utils
                            )
                        )
                    ) from e
                else:
                    archive.writestr(
                        archive_path.replace(".mako", "").replace("Project", view.device_name(project)),
                        rendered_file
                    )
            else:
                archive.write(file, archive_path)
