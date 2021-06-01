from io import StringIO
from itertools import chain
from os.path import abspath, dirname, join
from re import sub
from textwrap import indent, dedent
from zipfile import ZipFile, ZIP_DEFLATED

from urpc import ast
from urpc.builder.device.utils.namespaced import namespaced as namespaced_global
from urpc.builder.documentation.sphinx.static import get_ru_static_part, get_static_part
from urpc.builder.util.clang import split_by_type, get_argstructs
from urpc.util.cconv import ascii_to_hex, get_msg_len, type_to_cstr
from urpc.builder.documentation.common import common_path
from version import BUILDER_VERSION

_module_path = abspath(dirname(__file__))


def _prepare_text_sphinx(text):
    out = sub('["`]', "'", text)
    out = out.replace("\n", " ")
    out = out.replace("\r", " ")
    return out


def _get_description(arg):
    return _prepare_text_sphinx(arg.description.get("english", ""))


def _get_description_ru(arg):
    return _prepare_text_sphinx(arg.description.get("russian", ""))


def _build_ru_file(protocol, out):
    out.write(get_ru_static_part(protocol))

    cache = set()

    # Because these translations are already in static.py
    # TODO: parse static.py for automatically exclude static.py duplications
    cache.add("**Answer:** (4 bytes)")
    cache.add("uint32_t")

    def write_ru_en_pair(en, ru):
        if en in cache:
            return  # Duplications prohibited
        if not en:
            return  # Ignore empty descriptions
        out.write('msgid "{0}"\n'.format(en))
        out.write('msgstr "{0}"\n'.format(ru))
        out.write("\n")
        cache.add(en)

    def write_en_en_pair(en):
        write_ru_en_pair(en, en)

    def write_descriptions(req):
        for arg in req.args:

            if arg.name == "reserved":
                write_ru_en_pair("Reserved ({0} bytes)".format(len(arg.type_)),
                                 "Зарезервировано ({0} байт)".format(len(arg.type_)))
                write_en_en_pair("Reserved [{0}]".format(len(arg.type_)))
            else:
                write_ru_en_pair(_get_description(arg), _get_description_ru(arg))
                write_en_en_pair(arg.name)
                write_en_en_pair(type_to_cstr(arg.type_)[0])

                for c in arg.consts:
                    write_ru_en_pair(_get_description(c), _get_description_ru(c))
                    write_en_en_pair(c.name)
                    write_en_en_pair("{0} - {1}".format(hex(c.value), c.name))

    write_ru_en_pair("Checksum", "Контрольная сумма")
    write_ru_en_pair("Command", "Команда")
    write_en_en_pair("CMD")
    write_en_en_pair("CRC")

    write_ru_en_pair(
        "About this document",
        "Об этом документе"
    )
    write_ru_en_pair(
        "Documentation generator version: {BUILDER_VERSION}.".format(BUILDER_VERSION=BUILDER_VERSION),
        "Версия генератора документации: {BUILDER_VERSION}.".format(BUILDER_VERSION=BUILDER_VERSION)
    )

    for cmd in protocol.commands:
        write_ru_en_pair("Command {0}".format(cmd.cid.upper()),
                         "Команда {0}".format(cmd.cid.upper()))

        write_ru_en_pair('**Command code (CMD)**: \\"{0}\\" or {1}.'.format(cmd.cid, ascii_to_hex(cmd.cid)),
                         '**Код команды (CMD)**: \\"{0}\\" или {1}.'.format(cmd.cid, ascii_to_hex(cmd.cid)))

        write_ru_en_pair("**Description:** {0}".format(_get_description(cmd)),
                         "**Описание:** {0}".format(_get_description_ru(cmd)))

        write_ru_en_pair("**Answer:** ({0} bytes)".format(get_msg_len(cmd.response)),
                         "**Ответ:** ({0} байт)".format(get_msg_len(cmd.response)))

        write_ru_en_pair("**Request:** ({0} bytes)".format(get_msg_len(cmd.request)),
                         "**Запрос:** ({0} байт)".format(get_msg_len(cmd.request)))

        write_en_en_pair(cmd.name)

        write_descriptions(cmd.request)
        write_descriptions(cmd.response)


def _build_en_file(protocol, out, namespaced):
    simple_commands, accessors = split_by_type(protocol.commands)
    simple_commands, accessors = list(simple_commands), list(accessors)
    argstructs = get_argstructs(simple_commands, accessors)

    def inout(msg, argname):
        # take from base.textile.mako
        return ", " + namespaced(argstructs[msg].name) + "* " + argname if len(argstructs[msg].fields) else ""

    def message_fields(msg):

        def message_field(arg):
            base_type, length = type_to_cstr(arg.type_)
            return '"{0}", "{1}", "{2}"\n'.format(base_type, arg.name, _get_description(arg))

        out_l = StringIO()
        out_l.write('"{0}", "CMD", "Command"\n'.format(type_to_cstr(ast.Integer32u)[0]))
        for arg in msg.args:
            if arg.name == "reserved":
                out_l.write('"{0}", "Reserved [{1}]", "Reserved ({1} bytes)"\n'.format(type_to_cstr(ast.Integer8u)[0],
                                                                                       len(arg.type_)))
            else:
                out_l.write(message_field(arg))
            for c in arg.consts:
                out_l.write('"", "{0} - {1}", "{2}"\n'.format(hex(c.value), c.name, _get_description(c)))
        if len(msg.args) > 0:
            out_l.write('"{0}", "CRC", "Checksum"\n'.format(type_to_cstr(ast.Integer16u)[0]))

        return out_l.getvalue()

    def table_head():
        return dedent("""
        .. csv-table::
           :class: longtable
           :escape: \\
           :widths: 2, 8, 6
        """)

    out.write(get_static_part(protocol))  # write static part

    def _sort(commands):
        return sorted(commands, key=lambda command: command.cid)

    for cmd in chain(_sort([command for pair in accessors for command in pair]), _sort(simple_commands)):
        out.write("Command {0}\n".format(cmd.cid.upper()))
        out.write("~~~~~~~~~~~~\n")
        out.write("\n")
        out.write(".. code-block:: c\n")
        out.write("\n")
        func = "result_t " + namespaced(cmd.name) + "(device_t id" + inout(cmd.request, "input") + \
               inout(cmd.response, "output") + ")"
        out.write(indent(func, "   ") + "\n")

        out.write("\n")
        out.write('**Command code (CMD)**: "{0}" or {1}.\n'.format(cmd.cid, ascii_to_hex(cmd.cid)))
        out.write("\n")
        out.write("**Request:** ({0} bytes)\n".format(get_msg_len(cmd.request)))
        out.write("\n")
        out.write(table_head())
        out.write("\n")
        out.write(indent(message_fields(cmd.request), "   "))
        out.write("\n")
        out.write("**Answer:** ({0} bytes)\n".format(get_msg_len(cmd.response)))
        out.write("\n")
        out.write(table_head())
        out.write("\n")
        out.write(indent(message_fields(cmd.response), "   "))
        out.write("\n")
        out.write("**Description:**\n")
        out.write("{0}\n".format(_get_description(cmd)))
        out.write("\n")

    out.write(
        dedent(
            """\
            About this document
            -------------------
            Documentation generator version: {BUILDER_VERSION}.
            """
        ).format(
            BUILDER_VERSION=BUILDER_VERSION
        )
    )


def build(protocol, out):
    def namespaced(string):
        return namespaced_global(string=string, context={
            "protocol": protocol,
            "is_namespaced": False
        })

    with ZipFile(out, "w", ZIP_DEFLATED) as archive:
        buffer = StringIO()
        _build_en_file(protocol, buffer, namespaced)
        archive.writestr(
            "{}.rst".format(protocol.name.lower()),
            buffer.getvalue()
        )
        buffer = StringIO()
        _build_ru_file(protocol, buffer)
        archive.writestr("{}.po".format(protocol.name.lower()), buffer.getvalue())
        archive.write(join(common_path, "Synch.png"), "Synch.png")
        archive.write(join(common_path, "crc.png"), "crc.png")
