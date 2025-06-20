from os.path import abspath, dirname
from zipfile import ZipFile, ZIP_DEFLATED

from urpc.builder.util import ClangView
from urpc.builder.util.clang import namespace_symbol
from urpc.util.cconv import ascii_to_hex, get_msg_len, type_to_cstr
from urpc import ast
from .static import get_static_part
from version import BUILDER_VERSION

_module_path = abspath(dirname(__file__))


class _MarkdownBuilderImpl(ClangView):
    def __init__(self, protocol):
        super().__init__(protocol)
        self.__protocol = protocol

        if len(self._accessors) == 0:
            self.__getters, self.__setters = [], []
        else:
            self.__getters, self.__setters = zip(*self._accessors)

    def _nsp(self, symbol: str):
        return namespace_symbol(self.__protocol, symbol)

    def _func_arg_str(self, name, msg):
        if len(msg.children) == 0:
            return ""
        argstruct = self._argstructs[msg]
        return ", {} *{}".format(self._nsp(argstruct.name), name)

    def _func_head(self, command):
        head = ""
        head += "result_t {}(device_t id".format(self._nsp(command.name))
        head += self._func_arg_str("input", command.request)
        head += self._func_arg_str("input", command.response)
        head += ")"
        return head

    def _message_field(self, arg):
        base_type, length = type_to_cstr(arg.type_)
        c_str = "| `" + base_type + "` "
        c_str += "| {} ".format(arg.name)
        c_str += length
        c_str += " | " + ("Зарезервировано" if "reserved" in arg.name else arg.description.get("russian", "")) + " |"
        return c_str

    def _message_fields(self, msg):
        markdown = ""
        markdown += "| Тип  | Поле | Описание |\n"
        markdown += "| ---- | ---- | -------- |\n"
        markdown += "| `{}` | CMD  | Идентификатор команды |\n".format("".join(type_to_cstr(ast.Integer32u)))
        for arg in msg.args:
            markdown += self._message_field(arg) + "\n"
            for c in arg.consts:
                markdown += "||| `{}` (`0x{:02X}`) - {}|\n".format(c.name, c.value, c.description.get("russian", ""))
        if len(msg.args) > 0:
            markdown += "| `uint16_t` | CRC | Контрольная сумма |\n"

        return markdown

    def _generate_command(self, cmd):
        markdown = ""
        markdown += "### Команда {} ({})\n\n".format(self._nsp(cmd.name), cmd.cid.upper())
        markdown += "\n```c\n{}\n```\n".format(self._func_head(cmd))
        markdown += "Код команды (CMD): `{}` или `{}`\n\n".format(cmd.cid, ascii_to_hex(cmd.cid))
        markdown += "**Запрос** ({} байт)\n\n".format(get_msg_len(cmd.request))
        markdown += self._message_fields(cmd.request) + "\n"
        markdown += "**Ответ** ({} байт)\n\n".format(get_msg_len(cmd.response))
        markdown += self._message_fields(cmd.response) + "\n"
        markdown += "**Описание**\n"
        markdown += cmd.description.get("russian", "") + "\n"
        return markdown

    def generate_markdown(self):
        markdown = get_static_part() + "\n"
        for cmd in self._commands:
            markdown += self._generate_command(cmd) + "\n"
        if self.__getters != [] and self.__setters != []:
            for cmd in self.__getters:
                markdown += self._generate_command(cmd) + "\n"
            for cmd in self.__setters:
                markdown += self._generate_command(cmd) + "\n"
        markdown += "\n---\nВерсия генератора " + BUILDER_VERSION
        return markdown


def build(project, output, lang):
    view = _MarkdownBuilderImpl(project)

    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "{}.md".format(project.name.lower()),
            view.generate_markdown()
        )
