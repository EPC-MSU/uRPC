from enum import Enum
from os.path import dirname, abspath, join, basename
from zipfile import ZipFile, ZIP_DEFLATED

from mako.lookup import TemplateLookup

from urpc.builder.util import ClangView
from urpc.builder.util.resource import resources
from urpc.util.cconv import get_msg_len, ascii_to_hex

_module_path = abspath(dirname(__file__))
_lookup = TemplateLookup((join(_module_path, "resources"),), input_encoding="utf-8", output_encoding="utf-8")


class _HandlerTypes(Enum):
    noinput = 0
    regular = 1
    setter = 2
    getter = 3


class _DeviceView(ClangView):
    def __init__(self, project):
        super().__init__(project)

        self.upper_device_name = project.name.upper()

        self._cmd_to_handler_type = {t: [] for t in _HandlerTypes}

        for acc in self._accessors:
            for cmd, type_ in zip(acc, (_HandlerTypes.getter, _HandlerTypes.setter)):
                self._cmd_to_handler_type[type_].append(cmd)

        for cmd in self._commands:
            empty_request = not len(cmd.request.children)
            type_ = _HandlerTypes.noinput if empty_request else _HandlerTypes.regular
            self._cmd_to_handler_type[type_].append(cmd)

    @staticmethod
    def _command_code(cid):
        return "{}_CMD".format(cid.upper())

    @staticmethod
    def _struct_code(uid):
        return uid.upper()

    @property
    def command_argstructs(self):
        for cmd in self._commands:
            empty_request = not len(cmd.request.children)
            if empty_request:
                continue
            struct_type = self._argstructs[cmd.request].name
            struct_code = self._struct_code(cmd.cid)
            yield (struct_type, struct_code)

    @property
    def accessor_argstructs(self):
        for (getter, setter) in self._accessors:
            empty_getter_response = not len(getter.response.children)
            empty_setter_request = not len(setter.request.children)
            if empty_getter_response and empty_setter_request:
                continue

            struct_type = self._argstructs[getter.request].name
            assert struct_type == self._argstructs[setter.request].name
            aid = getter.cid[1:]
            assert aid == setter.cid[1:]
            struct_code = self._struct_code(aid)

            yield (struct_type, struct_code)

    def accessors_count(self):
        return len(self._accessors)

    @property
    def command_codes(self):
        for cmd in self._project.children:
            yield (self._command_code(cmd.cid), ascii_to_hex(cmd.cid))

    @property
    def command_lengths(self):
        for cmd in self._project.children:
            yield self._command_code(cmd.cid), get_msg_len(cmd.request), get_msg_len(cmd.response)

    @property
    def noinput_handlers(self):
        for cmd in self._cmd_to_handler_type[_HandlerTypes.noinput]:
            cmd_code = self._command_code(cmd.cid)
            yield cmd_code

    @property
    def noinput_handlers_commands(self):
        for cmd in self._cmd_to_handler_type[_HandlerTypes.noinput]:
            yield (cmd)

    @property
    def regular_handlers(self):
        for cmd in self._cmd_to_handler_type[_HandlerTypes.regular]:
            cmd_code = self._command_code(cmd.cid)
            struct_type = self._argstructs[cmd.request].name
            struct_code = self._struct_code(cmd.cid)
            yield (cmd_code, struct_type, struct_code)

    @property
    def regular_handlers_commands(self):
        for cmd in self._cmd_to_handler_type[_HandlerTypes.regular]:
            yield (cmd)

    def _accessor_handlers(self, _type):
        assert _type is _HandlerTypes.getter or _type is _HandlerTypes.setter
        for cmd in self._cmd_to_handler_type[_type]:
            cmd_code = self._command_code(cmd.cid)
            struct_type = self._argstructs[cmd.request].name

            # as accessor command pairs are guaranteed to have exactly the same argument structure
            # it can be uniquely identified only by 3 last symbols of commands' cid known as aid(accessor id)
            struct_code = self._struct_code(cmd.cid[1:])
            yield (cmd_code, struct_type, struct_code)

    def _accessor_handlers_commands(self, _type):
        assert _type is _HandlerTypes.getter or _type is _HandlerTypes.setter
        for cmd in self._cmd_to_handler_type[_type]:
            yield (cmd)

    @property
    def getter_handlers(self):
        for cmd_code, _, struct_code in self._accessor_handlers(_HandlerTypes.getter):
            yield cmd_code, struct_code

    @property
    def getter_handlers_commands(self):
        for cmd in self._accessor_handlers_commands(_HandlerTypes.getter):
            yield (cmd)

    @property
    def setter_handlers(self):
        yield from self._accessor_handlers(_HandlerTypes.setter)

    @property
    def setter_handlers_commands(self):
        yield from self._accessor_handlers_commands(_HandlerTypes.setter)


def build(protocol, output, path_mapping, is_namespaced):
    view = _DeviceView(protocol)

    utils = {
        "BUILDER_VERSION_MAJOR": view.BUILDER_VERSION_MAJOR,
        "BUILDER_VERSION_MINOR": view.BUILDER_VERSION_MINOR,
        "BUILDER_VERSION_BUGFIX": view.BUILDER_VERSION_BUGFIX,
        "BUILDER_VERSION_SUFFIX": view.BUILDER_VERSION_SUFFIX,
        "BUILDER_VERSION": view.BUILDER_VERSION,

        "upper_device_name": view.upper_device_name
    }

    subdir_path = join(_module_path, "resources")
    for file in resources(subdir_path):
        input_rel_path = file[len(subdir_path) + 1:]
        if basename(input_rel_path) in path_mapping:
            """If you set the if 1: condition instead and uncomment all the lines in default_path_mapping, then
               the FreeRTOS files will also be present in the abstract devices.
            """
            output_rel_path = path_mapping[basename(input_rel_path)] if basename(input_rel_path) in path_mapping \
                else input_rel_path

            if file.endswith(".mako"):
                # if "Project.cpp.mako" in file or "Project.h.mako" in file:
                output.writestr(output_rel_path.replace(".mako", ""),
                                _lookup.get_template(input_rel_path).render_unicode(view=view,
                                                                                    protocol=protocol,
                                                                                    is_namespaced=is_namespaced,
                                                                                    **utils))
            else:
                output.write(file, output_rel_path)


default_path_mapping = {
    join("algorithm.c"): join("src", "algorithm.c"),
    join("algorithm.h"): join("src", "algorithm.h"),
    join("commands.c.mako"): join("src", "commands.c.mako"),
    join("commands.h.mako"): join("src", "commands.h.mako"),
    join("flowparser.c.mako"): join("src", "flowparser.c.mako"),
    join("flowparser.h"): join("src", "flowparser.h"),
    join("handlers.c.mako"): join("src", "handlers.c.mako"),
    join("handlers.h.mako"): join("src", "handlers.h.mako"),
    join("iobuffer.c"): join("src", "iobuffer.c"),
    join("iobuffer.h"): join("src", "iobuffer.h"),
    join("macro.h"): join("src", "macro.h"),
    # join("croutine.c"): join("firmware", "src", "croutine.c"),
    # join("croutine.h"): join("firmware", "inc", "croutine.h"),
    join("version.h.mako"): join("src", "version.h"),
    join("version_raw.h.mako"): join("src", "version_raw.h"),
    # join("deprecated_definitions.h"): join("firmware", "inc", "deprecated_definitions.h"),
    # join("event_groups.h"): join("firmware", "inc", "event_groups.h"),
    # join("FreeRTOS.h"): join("firmware", "inc", "FreeRTOS.h"),
    # join("heap_1.c"): join("firmware", "src", "heap_1.c"),
    # join("list.c"): join("firmware", "src", "list.c"),
    # join("list.h"): join("firmware", "inc", "list.h"),
    # join("message_buffer.h"): join("firmware", "inc", "message_buffer.h"),
    # join("mpu_prototypes.h"): join("firmware", "inc", "mpu_prototypes.h"),
    # join("mpu_wrappers.h"): join("firmware", "inc", "mpu_wrappers.h"),
    # join("pdc.h"): join("firmware", "inc", "pdc.h"),
    # join("portable.h"): join("firmware", "inc", "portable.h"),
    # join("portmacro.h"): join("firmware", "inc", "portmacro.h"),
    # join("projdefs.h"): join("firmware", "inc", "projdefs.h"),
    # join("queue.c"): join("firmware", "src", "queue.c"),
    # join("queue.h"): join("firmware", "inc", "queue.h"),
    # join("semphr.h"): join("firmware", "inc", "semphr.h"),
    # join("stack_macros.h"): join("firmware", "inc", "stack_macros.h"),
    # join("StackMacros.h"): join("firmware", "inc", "StackMacros.h"),
    # join("stream_buffer.h"): join("firmware", "inc", "stream_buffer.h"),
    # join("task.h"): join("firmware", "inc", "task.h"),
    # join("tasks.c"): join("firmware", "src", "tasks.c"),
    # join("timers.c"): join("firmware", "src", "timers.c"),
    # join("timers.h"): join("firmware", "inc", "timers.h"),
}


def build_full(protocol, output, is_namespaced):
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        build(protocol, archive, path_mapping=default_path_mapping, is_namespaced=is_namespaced)
