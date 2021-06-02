"""
This module generates Python profiles only for the libximc library, because
the protocol file format and URPC protocol files are not compatible and
the bindings used in the libraries are different.
"""
from io import StringIO
from json import loads
from textwrap import dedent, indent
from zipfile import ZipFile, ZIP_DEFLATED
from inflection import camelize, underscore

from urpc import ast
from urpc.builder.device.utils.namespaced import namespaced as namespaced_global
from urpc.builder.util.clang import split_by_type, get_argstructs
from urpc.util.cconv import type_to_cstr


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


def __style_flags(output, arg, value, namespaced, style="urmc"):
    # complex algorithm is necessary for reading 2 types of flags, see #17278-6
    flags = []
    if style == "ximc":
        output.write("    class {field}_:\n".format(field=arg.name))

    for const in sorted(arg.consts, key=lambda c: c.value, reverse=True):
        if style == "ximc":
            output.write("        {field} = {value}\n".format(field=const.name, value=const.value))

        if const.value & value == const.value:
            flags.append(const.name)
            value -= const.value

    return flags


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


def _write_assembly(protocol, output, profile_name, inc_guard, namespaced, style="urmc"):
    if style == "ximc":
        output.write(dedent("""\
            def {func_name}(lib, id):
                worst_result = Result.Ok
                result = Result.Ok\n\n""".format(func_name="set_profile_" + profile_name)))
    elif style == "urmc":
        output.write(dedent("""\
            def {func_name}(modul):
                worst_result = 0\n\n""".format(func_name="set_profile_" + profile_name)))


def _c_struct(command, argstructs):
    return argstructs[command.response].name


def write_command(output, namespaced, cmd, argstructs, style="urmc"):
    output.write(indent(dedent("""\
        {name} = {struct}()
    \n""".format(struct=style_camelize_arg(_c_struct(cmd, argstructs), style), name=_accessor_name(cmd))), "    "))


def unsig(value):
    if value < 0:
        return 256 + value
    return value


def style_underscore_arg(name, style="urmc"):
    return name if style == "ximc" else underscore(name)


def style_camelize_arg(name, style="urmc"):
    return name if style == "ximc" else "modul."+camelize(name[:-2])+"Request"


def write_argument_array(arg, profile_command, output, cmd, style="urmc"):
    if _c_type(arg.type_) in ("char", "int8_t"):
        values = "bytes([" + str.join(", ", [str(unsig(val)) for val in profile_command[arg.name]]) + "])"
        output.write("    {name}.{field} = {values}\n".format(name=_accessor_name(cmd),
                                                              field=style_underscore_arg(arg.name, style),
                                                              values=values))
    else:
        for i in range(len(arg.type_)):
            output.write("    {name}.{field}[{i}] = {value}\n".format(name=_accessor_name(cmd),
                                                                      field=style_underscore_arg(arg.name, style),
                                                                      i=i,
                                                                      value=profile_command[arg.name][i]))


def style_write_argument_scalar(arg, profile_command, namespaced, cmd, output, style="urmc"):
    if len(arg.consts):
        value = __style_flags(output, arg, profile_command[arg.name], namespaced, style)
        # print(profile_command[arg.name], arg.name)
        counter = 1
        for flag in value:
            if counter:
                if style == "ximc":
                    output.write("    {name}.{field} = {field1}_.{value}".format(name=_accessor_name(cmd),
                                                                                 field=style_underscore_arg(arg.name,
                                                                                                            style),
                                                                                 field1=arg.name,
                                                                                 value=flag))
                elif style == "urmc":
                    output.write("    {name}.{field} = {name}.{field1}.{value}".format(name=_accessor_name(cmd),
                                                                                       field=style_underscore_arg(
                                                                                           arg.name, style),
                                                                                       field1=arg.name,
                                                                                       value=flag))
            else:
                if style == "ximc":
                    output.write(" | {field}_.{value}".format(field=arg.name,
                                                              value=flag))
                elif style == "urmc":
                    output.write(" | {name}.{field}.{value}".format(name=_accessor_name(cmd),
                                                                    field=arg.name,
                                                                    value=flag))
            counter = 0
        output.write("\n")
    else:
        value = profile_command[arg.name]
        output.write("    {name}.{field} = {value}\n".format(name=_accessor_name(cmd),
                                                             field=style_underscore_arg(arg.name, style),
                                                             value=value))


def style_write_argument(arg, profile_command, namespaced, output, cmd, style="urmc"):
    if isinstance(arg.type_, ast.ArrayType):
        write_argument_array(arg, profile_command, output, cmd, style)
    else:
        style_write_argument_scalar(arg, profile_command, namespaced, cmd, output, style)


def write_call(output, namespaced, cmd, style="urmc"):
    if style == "ximc":
        output.write(indent(dedent("""\
                result = {func}(id, byref({struct}))

                if result != Result.Ok:
                    if worst_result == Result.Ok or worst_result == Result.ValueError:
                        worst_result = result
         \n""".format(func="lib.set_" + _accessor_name(cmd), struct=_accessor_name(cmd))), "    "))
    elif style == "urmc":
        output.write(indent(dedent("""\
                        {func}({struct})
                 \n""".format(func="modul.set_" + _accessor_name(cmd), struct=_accessor_name(cmd))), "    "))


def _style_assembly(name, profile, protocol, namespaced, style="urmc"):
    profile = loads(profile.decode("utf-8"))

    output = StringIO()

    profile_name = _fix_profile_name(name)

    inc_guard = "__" + profile_name.upper()

    _write_assembly(protocol, output, profile_name, inc_guard, namespaced, style)

    argstructs = _argstructs(protocol)

    for cmd in _accessors(protocol):
        if _accessor_name(cmd) not in profile:
            continue
        if len(_args(cmd)) == 1:
            continue

        profile_command = profile[_accessor_name(cmd)]

        # skip command if empty or reserved only
        if len(profile_command) == 0 or list(profile_command.keys()) == ["reserved"]:
            continue

        write_command(output, namespaced, cmd, argstructs, style)

        for arg in _args(cmd):
            # skip argument if not exist and "reserved" arguments
            if arg.name not in profile_command:
                continue
            if arg.name == "reserved":
                continue

            try:
                style_write_argument(arg, profile_command, namespaced, output, cmd, style)
            except KeyError:
                pass
            except ValueError:
                pass

        write_call(output, namespaced, cmd, style)

    output.write("    return worst_result\n")
#    output.write("}\n\n")

    return output.getvalue()


def style_build(project, profiles, output, is_namespaced, style="urmc"):
    def namespaced(string):
        return namespaced_global(string=string, context={
            "protocol": project,
            "is_namespaced": is_namespaced
        })

    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for name, contain in profiles:
            archive.writestr(name.replace(".json", ".py"), _style_assembly(name, contain, project, namespaced, style))
