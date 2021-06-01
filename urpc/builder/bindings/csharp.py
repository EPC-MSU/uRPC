from zipfile import ZipFile, ZIP_DEFLATED
from urpc import ast
from io import StringIO
from textwrap import dedent, indent
from urpc.builder.util.clang import split_by_type, get_argstructs, non_empty_unique_argstructs_iter, flagset_arg_iter, \
    library_shared_file, namespace_symbol

from version import BUILDER_VERSION_MAJOR, BUILDER_VERSION_MINOR, BUILDER_VERSION_BUGFIX, BUILDER_VERSION_SUFFIX, \
    BUILDER_VERSION


def _get_csharp_type(t):
    if t == ast.Integer8u:
        return "byte"
    elif t == ast.Integer8s:
        return "sbyte"
    elif t == ast.Integer16u:
        return "ushort"
    elif t == ast.Integer16s:
        return "short"
    elif t == ast.Integer32u:
        return "uint"
    elif t == ast.Integer32s:
        return "int"
    elif t == ast.Integer64u:
        return "ulong"
    elif t == ast.Integer64s:
        return "long"
    elif t == ast.Float:
        return "float"
    elif isinstance(t, ast.Array):
        return "{}[]".format(_get_csharp_type(t.type))
    else:
        raise ValueError("Has no know type conversion")


def build(protocol, out):
    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        buffer = StringIO()
        _build_file(protocol, buffer)
        archive.writestr(
            "{}.cs".format(protocol.name.lower()),
            buffer.getvalue()
        )


def _build_file(protocol, out):
    simple_commands, accessors = split_by_type(protocol.commands)
    simple_commands, accessors = list(simple_commands), list(accessors)
    argstructs = get_argstructs(simple_commands, accessors)

    def build_flags():
        out.write(indent("[Flags] public enum Flags : uint {\n", "\t"))
        seen_consts = {}
        for arg in flagset_arg_iter(simple_commands, accessors):
            for const in arg.consts:
                # HACK: implicitly assume that if const names are the same than they always have the same value
                # The same assumption is made in C client library, but is achieved via #define behaviour
                if const.name in seen_consts:
                    if seen_consts[const.name].value != const.value:
                        raise ValueError("Non-unique name flag constant value equality assumption violation")
                    continue
                seen_consts[const.name] = const
                out.write(indent("{} = {},\n".format(const.name, const.value), "\t" * 2))
        out.write(indent("}\n", "\t"))

    def build_argstructs():
        for struct in non_empty_unique_argstructs_iter(argstructs.values()):
            out.write(indent(dedent("""\
                [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Ansi)]
                public struct {} {{
            """.format(struct.name)), "\t"))
            for arg in struct.args:
                field = "{} {}".format(_get_csharp_type(arg.type), arg.name)
                if isinstance(arg.type, ast.Array):
                    out.write(indent(
                        "[MarshalAs(UnmanagedType.ByValArray, SizeConst = {})]\n".format(len(arg.type)),
                        "\t" * 2)
                    )
                out.write(indent("public {};\n".format(field), "\t" * 2))
            out.write(indent("};\n", "\t"))

    def build_commands():
        libfile = library_shared_file(protocol)

        out.write(indent("public partial class API {\n", "\t"))
        out.write(indent(dedent("""\
            [DllImport("{libfile}", CharSet = CharSet.Ansi, CallingConvention=CallingConvention.Cdecl)]
            public static extern int {func_name}([MarshalAs(UnmanagedType.LPStr)] String name);
        """).format(
            libfile=libfile,
            func_name=namespace_symbol(protocol, "open_device")
        ), "\t" * 2))
        out.write(indent(dedent("""\
                    [DllImport("{libfile}", CharSet = CharSet.Ansi, CallingConvention=CallingConvention.Cdecl)]
                    public static extern int {func_name}([MarshalAs(UnmanagedType.LPStr)] String libver);
                ''').format(
            libfile=libfile,
            func_name=namespace_symbol(protocol, "lib_version")
        ), "\t" * 2))
        out.write(indent(dedent('''\
            [DllImport("{libfile}", CallingConvention=CallingConvention.Cdecl)]
            public static extern Result {func_name}(ref int id);
        """).format(
            libfile=libfile,
            func_name=namespace_symbol(protocol, "close_device")
        ), "\t" * 2))

        for cmd in protocol.commands:
            args = []

            request_argstruct = argstructs[cmd.request]
            if request_argstruct.empty:
                args.append("ref {} input".format(request_argstruct.name))

            response_argstruct = argstructs[cmd.response]
            if response_argstruct.empty:
                args.append("out {} output".format(response_argstruct.name))

            out.write(indent(dedent("""\
                [DllImport("{libfile}", CallingConvention=CallingConvention.Cdecl)]
                public static extern Result {func_name}(int id{args});
            """).format(
                libfile=libfile,
                func_name=namespace_symbol(protocol, cmd.name),
                args="".join(", " + a for a in args)
            ), "\t" * 2))

        out.write(indent("};", "\t"))

    out.write(dedent("""\
        using System;
        using System.Runtime.InteropServices;
        using System.Text;

        namespace {} {{
    """.format(protocol.name.lower())))

    out.write(indent(dedent("""\
        public enum Result {
            ok = 0,
            error = -1,
            not_implemented = -2,
            value_error = -3,
            no_device = -4
        };
    """), "\t"))

    out.write(indent(dedent("""\
        public static class UrpcBuilderVersion {{
            public const int major = {BUILDER_VERSION_MAJOR};
            public const int minor = {BUILDER_VERSION_MINOR};
            public const int bugfix = {BUILDER_VERSION_BUGFIX};
            public const String suffix = "{BUILDER_VERSION_SUFFIX}";
            public const String version = "{BUILDER_VERSION}";
        }};
    """), "\t").format(
        BUILDER_VERSION_MAJOR=BUILDER_VERSION_MAJOR,
        BUILDER_VERSION_MINOR=BUILDER_VERSION_MINOR,
        BUILDER_VERSION_BUGFIX=BUILDER_VERSION_BUGFIX,
        BUILDER_VERSION_SUFFIX=BUILDER_VERSION_SUFFIX,
        BUILDER_VERSION=BUILDER_VERSION
    ))

    build_flags()
    build_argstructs()
    build_commands()

    out.write("\n};")


def init():
    # Empty function for flake 8
    return None
