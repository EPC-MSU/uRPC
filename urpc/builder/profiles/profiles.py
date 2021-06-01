from io import StringIO
from json import loads
from textwrap import dedent, indent
from zipfile import ZipFile, ZIP_DEFLATED

from urpc import ast
from urpc.builder.device.utils.namespaced import namespaced as namespaced_global
from urpc.builder.util.clang import split_by_type, get_argstructs, library_header_file
from urpc.util.cconv import type_to_cstr
from version import BUILDER_VERSION_MAJOR, BUILDER_VERSION_MINOR, BUILDER_VERSION_BUGFIX, BUILDER_VERSION_SUFFIX, \
    BUILDER_VERSION


def _argstructs(protocol):
    simple_commands, accessors = split_by_type(protocol.commands)
    simple_commands, accessors = list(simple_commands), list(accessors)
    return get_argstructs(simple_commands, accessors)


def _accessor_name(cmd):
    return cmd.name.replace("get_", "")


def _args(cmd):
    return cmd.response.args


def _accessors(protocol):
    _, accessors = split_by_type(protocol.commands)
    accessors = list(accessors)
    for getter, _ in accessors:
        yield getter


def _c_flags(arg, value, namespaced):
    # complex algorithm is necessary for reading 2 types of flags, see #17278-6
    flags = []
    for const in sorted(arg.consts, key=lambda c: c.value, reverse=True):
        if const.value & value == const.value:
            flags.append(namespaced(const.name))
            value -= const.value
    if len(flags):
        output = str.join(" | ", flags)
    else:
        output = "0"

    return output


def _c_type(argtype):
    return type_to_cstr(argtype)[0]


def _fix_profile_name(name):
    symbols_map = {
        "-": "_",
        "@": "",
        "(": "",
        ")": "",
        "№": "",
        "%": "",
        ":": "",
        "^": "",
        "&": "",
        "?": "",
        ".": "",
        "*": "",
        "~": "",
        "+": "",
        "!": "",
        "#": "",
        "$": "",
    }

    out = name.replace(".json", "")
    for s in symbols_map.keys():
        out = out.replace(s, symbols_map[s])
    return out


def _write_assembly(protocol, output, profile_name, inc_guard, namespaced):
    output.write(dedent("""\
        #ifndef {inc_guard}
        #define {inc_guard}

        #include <string.h>

        #if defined(__APPLE__) && !defined(NOFRAMEWORK)
        #include <{lib_name}/{lib_header}>
        #else
        #include <{lib_header}>
        #endif


        #define {upper_device_name}_BUILDER_VERSION_MAJOR  {BUILDER_VERSION_MAJOR}
        #define {upper_device_name}_BUILDER_VERSION_MINOR  {BUILDER_VERSION_MINOR}
        #define {upper_device_name}_BUILDER_VERSION_BUGFIX {BUILDER_VERSION_BUGFIX}
        #define {upper_device_name}_BUILDER_VERSION_SUFFIX "{BUILDER_VERSION_SUFFIX}"
        #define {upper_device_name}_BUILDER_VERSION        "{BUILDER_VERSION}"


        """).format(
        upper_device_name=profile_name.upper(),
        BUILDER_VERSION_MAJOR=BUILDER_VERSION_MAJOR,
        BUILDER_VERSION_MINOR=BUILDER_VERSION_MINOR,
        BUILDER_VERSION_BUGFIX=BUILDER_VERSION_BUGFIX,
        BUILDER_VERSION_SUFFIX=BUILDER_VERSION_SUFFIX,
        BUILDER_VERSION=BUILDER_VERSION,
        inc_guard=inc_guard,
        lib_name="lib" + library_header_file(protocol),
        lib_header=library_header_file(protocol) + ".h")
    )

    output.write(dedent("""\
        #if defined(_MSC_VER)
        #define inline __inline
        #endif\n\n"""))

    output.write(dedent("""\
        static inline result_t {func_name}(device_t id)
        {{
          result_t worst_result = result_ok;
          result_t result = result_ok;\n\n""".format(func_name=namespaced("set_profile_") + profile_name)))


def _c_struct(command, argstructs):
    return argstructs[command.response].name


def write_command(output, namespaced, cmd, argstructs):
    output.write(indent(dedent("""\
    {struct} {name};
    memset((void*)&{name}, 0, sizeof({struct}));\n""".format(struct=namespaced(_c_struct(cmd, argstructs)),
                                                             name=_accessor_name(cmd))), "  "))


def write_argument_array(arg, profile_command, output, cmd):
    if _c_type(arg.type_) in ("char", "uint8_t", "int8_t"):
        values = "{" + str.join(", ", [str(val) for val in profile_command[arg.name]]) + "}"
        size_str = "sizeof(" + _c_type(arg.type_) + ") * " + str(len(arg.type_))
        output.write("  const {type} {name}_{field}_temp[{size}] = {values};\n".format(type=_c_type(arg.type_),
                                                                                       name=_accessor_name(cmd),
                                                                                       field=arg.name,
                                                                                       size=len(arg.type_),
                                                                                       values=values))
        output.write("  memcpy({name}.{field}, {name}_{field}_temp, {size});\n".format(name=_accessor_name(cmd),
                                                                                       field=arg.name,
                                                                                       size=size_str))
    else:
        for i in range(len(arg.type_)):
            output.write("  {name}.{field}[{i}] = {value};\n".format(name=_accessor_name(cmd),
                                                                     field=arg.name,
                                                                     i=i,
                                                                     value=profile_command[arg.name][i]))


def write_argument_scalar(arg, profile_command, namespaced, cmd, output):
    if len(arg.consts):
        value = _c_flags(arg, profile_command[arg.name], namespaced)
    else:
        value = profile_command[arg.name]

    output.write("  {name}.{field} = {value};\n".format(name=_accessor_name(cmd),
                                                        field=arg.name,
                                                        value=value))


def write_argument(arg, profile_command, namespaced, output, cmd):
    if isinstance(arg.type_, ast.ArrayType):
        write_argument_array(arg, profile_command, output, cmd)
    else:
        write_argument_scalar(arg, profile_command, namespaced, cmd, output)


def write_call(output, namespaced, cmd):
    output.write(indent(dedent("""\
      result = {func}(id, &{struct});

      if (result != result_ok)
      {{
        if (worst_result == result_ok || worst_result == result_value_error)
        {{
          worst_result = result;
        }}
      }}\n
      """.format(func=namespaced("set_" + _accessor_name(cmd)), struct=_accessor_name(cmd))), "  "))


def _assembly(name, profile, protocol, namespaced):
    profile = loads(profile.decode("utf-8"))

    output = StringIO()

    profile_name = _fix_profile_name(name)

    inc_guard = "__" + profile_name.upper()

    _write_assembly(protocol, output, profile_name, inc_guard, namespaced)

    argstructs = _argstructs(protocol)

    for cmd in _accessors(protocol):
        if _accessor_name(cmd) not in profile:
            continue

        profile_command = profile[_accessor_name(cmd)]

        # skip command if empty or reserved only
        if len(profile_command) == 0 or list(profile_command.keys()) == ["reserved"]:
            continue

        write_command(output, namespaced, cmd, argstructs)

        for arg in _args(cmd):
            # skip argument if not exist and "reserved" arguments
            if arg.name not in profile_command:
                continue
            if arg.name == "reserved":
                continue

            try:
                write_argument(arg, profile_command, namespaced, output, cmd)
            except KeyError:
                pass
            except ValueError:
                pass

        write_call(output, namespaced, cmd)

    output.write("  return worst_result;\n")
    output.write("}\n\n")
    output.write("#endif\n")

    return output.getvalue()


def build(project, profiles, output, is_namespaced):
    def namespaced(string):
        return namespaced_global(string=string, context={
            "protocol": project,
            "is_namespaced": is_namespaced
        })

    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, contain in profiles:
            archive.writestr(name.replace(".json", ".h"), _assembly(name, contain, project, namespaced))
