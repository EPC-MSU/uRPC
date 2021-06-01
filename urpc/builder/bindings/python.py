from zipfile import ZipFile, ZIP_DEFLATED
from urpc import ast
from io import StringIO
from textwrap import dedent, indent
from bunch import Bunch
from inflection import camelize, underscore
from urpc.builder.util.clang import split_by_type, get_argstructs, namespace_symbol

from version import BUILDER_VERSION_MAJOR, BUILDER_VERSION_MINOR, BUILDER_VERSION_BUGFIX, BUILDER_VERSION_SUFFIX, \
    BUILDER_VERSION


# TODO: Add all Python keywords from 'keyword' module
_reserved_vars = Bunch(
    request_buffer="src_buffer",
    response_buffer="dst_buffer"
)


# https://docs.python.org/3.4/library/ctypes.html#fundamental-data-types
def _get_python_type(t, for_input=False):
    def get_python_type(t):
        if t in (
                ast.Integer8u,
                ast.Integer8s,
                ast.Integer16s,
                ast.Integer16u,
                ast.Integer32u,
                ast.Integer32s,
                ast.Integer64u,
                ast.Integer64s
        ):
            return "int"
        elif t is ast.Float:
            return "float"
        elif isinstance(t, ast.Array):
            return "Sequence[{}]".format(get_python_type(t.type))
        else:
            raise ValueError("Has no know type conversion")

    if for_input:
        return "Union[{}, {}]".format(get_python_type(t), _get_python_ctype(t))
    else:
        return _get_python_ctype(t)


def _get_python_ctype(t):
    if t == ast.Integer8u:
        return "c_ubyte"
    elif t == ast.Integer8s:
        return "c_byte"
    elif t == ast.Integer16u:
        return "c_ushort"
    elif t == ast.Integer16s:
        return "c_short"
    elif t == ast.Integer32u:
        return "c_uint"
    elif t == ast.Integer32s:
        return "c_int"
    elif t == ast.Integer64u:
        return "c_ulonglong"
    elif t == ast.Integer64s:
        return "c_longlong"
    elif t == ast.Float:
        return "c_float"
    elif isinstance(t, ast.Array):
        return "{}*{}".format(_get_python_ctype(t.type), len(t))
    else:
        raise ValueError("Has no know type conversion")


def _is_reserved_arg(arg):
    # TODO: more sane way to mark unused fields
    return "reserved" in arg.name


def _nonreserved_request_args(cmd):
    for arg in cmd.request.args:
        if _is_reserved_arg(arg):
            continue
        yield arg


def _return_type_annotation(out_struct_class_name, response_has_payload):
    return out_struct_class_name if response_has_payload else "None"


def _pythonic_arg_name(arg):
    return underscore(arg.name)


def build_implicit_struct_overload(response_has_payload, out_struct_class_name, out, method_name, cmd):
    def method_arg_strings():
        yield "self"
        for arg in _nonreserved_request_args(cmd):
            name = _pythonic_arg_name(arg)
            yield "{}: {}".format(
                name,
                _get_python_type(arg.type, for_input=True)
            )
        if response_has_payload:
            yield "*"
            yield "{}: Optional[{}]=None".format(
                _reserved_vars.response_buffer,
                out_struct_class_name
            )

    out.write(indent(dedent("""\
        @overload
        def {}({}) -> {}: pass
    """).format(
        method_name,
        "\n" + ",\n".join((" " * 8) + a for a in method_arg_strings()) + "\n",
        _return_type_annotation(out_struct_class_name, response_has_payload)
    ), " " * 4))


def build_explicit_struct_overload(request_has_payload, response_has_payload,
                                   in_struct_class_name, out_struct_class_name,
                                   out, method_name):
    def method_arg_strings():
        yield "self"
        if request_has_payload:
            yield "{}: {}".format(_reserved_vars.request_buffer, in_struct_class_name)
        if response_has_payload:
            yield "*"
            yield "{}: Optional[{}]=None".format(_reserved_vars.response_buffer, out_struct_class_name)

    out.write(indent(dedent("""\
        @overload
        def {}({}) -> {}: pass
    """).format(
        method_name,
        "\n" + ",\n".join((" " * 8) + a for a in method_arg_strings()) + "\n",
        _return_type_annotation(out_struct_class_name, response_has_payload)
    ), " " * 4))


def build_implementation(request_has_payload, response_has_payload,
                         out, method_name, in_struct_class_name,
                         out_struct_class_name, protocol, cmd):
    def method_arg_strings():
        yield "self"
        if request_has_payload:
            yield "*args"
        if response_has_payload:
            yield "**kwargs"

    def request_constructor_arg_strings():
        for i, a in enumerate(_nonreserved_request_args(cmd)):
            yield "{}=_normalize_arg(args[{}], {})".format(_pythonic_arg_name(a), i, _get_python_ctype(a.type))

    out.write(indent(dedent("""\
        def {method_name}({args}) -> {return_type}:
    """.format(
        method_name=method_name,
        args=", ".join(method_arg_strings()),
        return_type=_return_type_annotation(out_struct_class_name, response_has_payload)
    )), " " * 4))

    call_args = ["self._handle"]
    if request_has_payload:
        out.write(indent(dedent("""\
            {buffer_name} = None
            if len(args) != 1 or not isinstance(args[0], {buffer_class}):
                {buffer_name} = {buffer_class}({init_args})
            else:
                {buffer_name} = args[0]
        """).format(
            buffer_name=_reserved_vars.request_buffer,
            buffer_class="self.{}".format(in_struct_class_name),
            init_args="\n" + ",\n".join((" " * 8) + a for a in request_constructor_arg_strings()) + "\n" + (" " * 4)
        ), " " * 8))
        call_args.append("byref({})".format(_reserved_vars.request_buffer))

    if response_has_payload:
        out.write(indent(dedent("""\
            {buffer_name} = kwargs.get("{buffer_name}", {buffer_class}())
        """.format(
            buffer_name=_reserved_vars.response_buffer,
            buffer_class="self.{}".format(out_struct_class_name)
        )), " " * 8))
        call_args.append("byref({})".format(_reserved_vars.response_buffer))

    out.write(indent(dedent("""\
        _validate_call(_lib.{}({}))
    """).format(namespace_symbol(protocol, cmd.name), ", ".join(call_args)), " " * 8))

    if response_has_payload:
        out.write(indent(dedent("""\
            return {}
        """.format(
            _reserved_vars.response_buffer
        )), " " * 8))


def _build_method(protocol, cmd, in_struct_class_name, out_struct_class_name, out):
    request_has_payload, response_has_payload = len(cmd.request.args), len(cmd.response.args)
    method_name = underscore(cmd.name)

    if request_has_payload:
        build_implicit_struct_overload(response_has_payload, out_struct_class_name, out, method_name, cmd)
        out.write("\n")
        build_explicit_struct_overload(request_has_payload, response_has_payload,
                                       in_struct_class_name, out_struct_class_name,
                                       out, method_name)
        out.write("\n")
    build_implementation(request_has_payload, response_has_payload,
                         out, method_name, in_struct_class_name,
                         out_struct_class_name, protocol, cmd)
    out.write("\n")


def _build_methods(protocol, simple_commands, accessors, argstructs, out):
    def build_property(arg):
        if len(arg.consts):
            flagset_type_name = camelize(arg.name)

            out.write(indent("class {}(int):".format(flagset_type_name), " " * 8))
            out.write("\n")
            if len(arg.consts) == 0:
                out.write(indent("pass", " " * 12))
                out.write("\n")
                return

            for const in arg.consts:
                out.write(indent("{} = {}".format(const.name.upper(), const.value), " " * 12))
                out.write("\n")

            for const in arg.consts:
                out.write("\n")
                out.write(indent(dedent("""\
                    @property
                    def {}(self) -> int:
                        return self & self.{}\
                """).format(
                    underscore(const.name),
                    const.name.upper()
                ), " " * 12))
                out.write("\n")

            out.write("\n")

            out.write(indent(dedent("""\
                @property
                def {0}(self) -> {1}:
                    return self.{1}(self._{0})
            """).format(
                underscore(arg.name),
                flagset_type_name,
            ), " " * 8))
        else:
            out.write(indent(dedent("""\
                @property
                def {0}(self) -> {1}:
                    return self._{0}
            """).format(
                underscore(arg.name),
                _get_python_type(arg.type)
            ), " " * 8))
            out.write("\n")
        out.write(indent(dedent("""
            @{0}.setter
            def {0}(self, value: {1}) -> None:
                self._{0} = _normalize_arg(value, {2})
        """).format(
            underscore(arg.name),
            _get_python_type(arg.type, for_input=True),
            _get_python_ctype(arg.type)
        ), " " * 8))
        out.write("\n")

    def build_struct_class(name, msg):
        out.write(indent("class {}(_IterableStructure):\n".format(name), " " * 4))
        if len(msg.args) == 0:
            out.write(indent("pass\n", " " * 8))
            return
        out.write(indent("_fields_ = (\n", " " * 8))
        for arg in msg.args:
            out.write(indent("(\"{}\", {}),\n".format("_" + underscore(arg.name),
                                                      _get_python_ctype(arg.type)), " " * 12))
        out.write(indent(")\n\n", " " * 8))

        for arg in msg.args:
            build_property(arg)

    for cmd in simple_commands:
        struct_class_name = camelize(cmd.name)
        request_class_struct_name = struct_class_name + "Request"
        response_class_struct_name = struct_class_name + "Response"

        if len(cmd.request.args) != 0:
            build_struct_class(request_class_struct_name, cmd.request)
        if len(cmd.response.args) != 0:
            build_struct_class(response_class_struct_name, cmd.response)
        _build_method(protocol, cmd, request_class_struct_name, response_class_struct_name, out)

    for (getter, setter) in accessors:
        struct_class_name = camelize(argstructs[getter.response].name.strip("_t"))
        request_class_struct_name = struct_class_name + "Request"
        response_class_struct_name = struct_class_name + "Response"

        build_struct_class(request_class_struct_name, getter.response)
        out.write(indent("{} = {}\n\n".format(response_class_struct_name, request_class_struct_name), " " * 4))

        _build_method(protocol, getter, request_class_struct_name, response_class_struct_name, out)
        _build_method(protocol, setter, request_class_struct_name, response_class_struct_name, out)


def _build_file(protocol, out):
    simple_commands, accessors = split_by_type(protocol.commands)
    simple_commands, accessors = list(simple_commands), list(accessors)
    argstructs = get_argstructs(simple_commands, accessors)

    # TODO: embed actual builder version
    out.write(dedent("""\
        \"""
        Project generated by builder {BUILDER_VERSION}
        \"""
        import logging
        from sys import version_info
        from ctypes import CDLL, Structure, Array, CFUNCTYPE, byref, create_string_buffer, addressof, cast
        from ctypes import c_ubyte, c_byte, c_ushort, c_short, c_uint, c_int, c_ulonglong, c_longlong, c_float, \\
             c_void_p, c_char_p, c_wchar_p, c_size_t
        from ctypes.util import find_library
        import atexit
        try:
            from typing import overload, Union, Sequence, Optional
        except ImportError:
            def overload(method):
                return method
            class _GenericTypeMeta(type):
                def __getitem__(self, _):
                    return None
            class Union(metaclass=_GenericTypeMeta):
                pass
            class Sequence(metaclass=_GenericTypeMeta):
                pass
            class Optional(metaclass=_GenericTypeMeta):
                pass
        urpc_builder_version_major = {BUILDER_VERSION_MAJOR}
        urpc_builder_version_minor = {BUILDER_VERSION_MINOR}
        urpc_builder_version_bugfix = {BUILDER_VERSION_BUGFIX}
        urpc_builder_version_suffix = "{BUILDER_VERSION_SUFFIX}"
        urpc_builder_version = "{BUILDER_VERSION}"
        _Ok = 0
        _Error = -1
        _NotImplemented = -2
        _ValueError = -3
        _NoDevice = -4
        _DeviceUndefined = -1
        class _IterableStructure(Structure):
            def __iter__(self):
                return (getattr(self, n) for n, t in self._fields_)
        def _validate_call(result):
            if result == _ValueError:
                raise ValueError()
            elif result == _NotImplemented:
                raise NotImplementedError()
            elif result != _Ok:
                raise RuntimeError()
        def _normalize_arg(value, desired_ctype):
            from collections import Sequence
            if isinstance(value, desired_ctype):
                return value
            elif issubclass(desired_ctype, Array) and isinstance(value, Sequence):
                member_type = desired_ctype._type_
                if desired_ctype._length_ < len(value):
                    raise ValueError()
                if issubclass(member_type, c_ubyte) and isinstance(value, bytes):
                    return desired_ctype.from_buffer_copy(value)
                elif issubclass(member_type, c_ubyte) and isinstance(value, bytearray):
                    return desired_ctype.from_buffer(value)
                else:
                    return desired_ctype(*value)
            else:
                return desired_ctype(value)
    \n\n""").format(
        BUILDER_VERSION_MAJOR=BUILDER_VERSION_MAJOR,
        BUILDER_VERSION_MINOR=BUILDER_VERSION_MINOR,
        BUILDER_VERSION_BUGFIX=BUILDER_VERSION_BUGFIX,
        BUILDER_VERSION_SUFFIX=BUILDER_VERSION_SUFFIX,
        BUILDER_VERSION=BUILDER_VERSION
    ))

    out.write(dedent("""\
        def _load_lib():
            from platform import system
            lib = None
            os_kind = system().lower()
            if os_kind == "windows":
                lib = CDLL("{library_name}.dll")
            elif os_kind == "darwin":
                lib = CDLL("lib{library_name}.dylib")
            elif os_kind == "freebsd" or "linux" in os_kind:
                lib = CDLL("lib{library_name}.so")
            else:
                raise RuntimeError("unexpected OS")

            return lib

        _lib = _load_lib()
    \n\n""".format(library_name=protocol.name.lower())))

    out.write(dedent("""\
        # Hack to prevent auto-conversion to native Python int
        class _device_t(c_int):
            def from_param(self, *args):
                return self
        _lib.{}.restype = _device_t
    \n\n""".format(namespace_symbol(protocol, "open_device"))))

    out.write(dedent("""\
        _logger = logging.getLogger(__name__)
        @CFUNCTYPE(None, c_int, c_wchar_p, c_void_p)
        def _logging_callback(loglevel, message, user_data):
            if loglevel == 0x01:
                _logger.error(message)
            elif loglevel == 0x02:
                _logger.warning(message)
            elif loglevel == 0x03:
                _logger.info(message)
            elif loglevel == 0x04:
                _logger.debug(message)
        _lib.{set_logging_callback}(_logging_callback)
        atexit.register(lambda: _lib.{set_logging_callback}(None))
    \n\n""".format(
        set_logging_callback=namespace_symbol(protocol, "set_logging_callback")))
    )

    # TODO: fix in library first
    # out.write(dedent("""\
    #     def version():
    #         # version a buffer to hold a version string, 32 bytes is enough
    #         v = (c_char*32)()
    #         _validate_call(_lib.{}(byref(v)))
    #         return v
    # \n\n""".format(namespace_symbol(protocol, "version"))))

    out.write(dedent("""\
        def reset_locks():
            _validate_call(_lib.{}())
    \n\n""".format(namespace_symbol(protocol, "reset_locks"))))

    out.write(dedent("""\
        def fix_usbser_sys():
            _validate_call(_lib.{}())
    \n\n""".format(namespace_symbol(protocol, "fix_usbser_sys"))))

    out.write(dedent("class {}DeviceHandle:\n".format(protocol.name.title().replace(" ", ""))))

    _build_methods(protocol, simple_commands, accessors, argstructs, out)

    out.write(indent(dedent("""\
        def __init__(self, uri, defer_open=False):
            if isinstance(uri, str):
                uri = uri.encode("utf-8")
            if not isinstance(uri, (bytes, bytearray)):
                raise ValueError()
            self._uri = uri
            self._handle = None
            if not defer_open:
                self.open()
        if version_info >= (3, 4):
            def __del__(self):
                if self._handle:
                    self.close()
        @property
        def uri(self):
            return self._uri
    \n"""), " " * 4))

    out.write(indent(dedent("""\
        def open(self):
            if self._handle is not None:
                return False

            handle = _lib.{}(self._uri)
            if handle.value == _DeviceUndefined:
                raise RuntimeError()

            self._handle = handle
            return True
    \n""").format(namespace_symbol(protocol, "open_device")), " " * 4))

    out.write(indent(dedent("""\
        def lib_version(self):
            ver_lib = create_string_buffer(str.encode("00.00.00"))
            result = _lib.{}(ver_lib)
            if result != _Ok:
                raise RuntimeError()
            version_lib = ver_lib.value.decode("utf-8")
            return version_lib
        \n""").format(namespace_symbol(protocol, "libversion")), " " * 4))

    out.write(indent(dedent("""\
        def close(self):
            if self._handle is None:
                return False

            try:
                result = _lib.{}(byref(self._handle))
                if result != _Ok:
                    raise RuntimeError()
            except:
                raise
            else:
                return True
            finally:
                self._handle = None
    \n""").format(namespace_symbol(protocol, "close_device")), " " * 4))

    out.write(indent(dedent("""\
        def get_profile(self):
            buffer = c_char_p()
            @CFUNCTYPE(c_void_p, c_size_t)
            def allocate(size):
                # http://bugs.python.org/issue1574593
                return cast(create_string_buffer(size+1), c_void_p).value
            _validate_call(_lib.{}(self._handle, byref(buffer), allocate))
            return buffer.value.decode("utf-8")
    \n""").format(namespace_symbol(protocol, "get_profile")), " " * 4))

    out.write(indent(dedent("""\
        def set_profile(self, source):
            if isinstance(source, str):
                source = source.encode("utf-8")
            _validate_call(_lib.{}(self._handle, c_char_p(source), len(source)))
    """).format(namespace_symbol(protocol, "set_profile")), " " * 4))

    # out.write(dedent("""
    # if __name__ == "__main__":
    #     pass
    # \n"""))


# TODO: make web-editor call builder hooks to check invariants while editing
class PythonBindingsBuilder:
    def __init__(self):
        pass

    def __call__(self, protocol, out):
        # from sys import stdout
        with ZipFile(out, "w", ZIP_DEFLATED) as archive:
            buffer = StringIO()
            _build_file(protocol, buffer)
            archive.writestr(
                "{}.py".format(protocol.name.lower()),
                buffer.getvalue()
            )


def init():
    # Empty function for flake 8
    return None


build = PythonBindingsBuilder()
