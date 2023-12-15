from os.path import abspath, dirname, join
from zipfile import ZipFile, ZIP_DEFLATED

from urpc.builder.util import ClangView
from urpc.builder.util.clang import namespace_symbol
from urpc.util.cconv import ascii_to_hex, get_msg_len, type_to_cstr
from urpc.builder.documentation.common import common_path
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
        head += f"result_t {self._nsp(command.name)}(device_t id"
        head += self._func_arg_str("input", command.request)
        head += self._func_arg_str("input", command.response)
        head += ")"
        return head

    def _message_field(self, arg):
        base_type, length = type_to_cstr(arg.type_)
        c_str = "| " + base_type
        c_str += " | {} ".format(arg.name)
        c_str += length
        c_str += " | " + ("Зарезервировано" if "reserved" in arg.name else arg.description.get("russian", "")) + " |"
        return c_str

    def _message_fields(self, msg):
        markdown = ""
        markdown += f'| {"".join(type_to_cstr(ast.Integer32u)) } | CMD | Команда |\n'
        markdown += '|---|---|---|\n'
        for arg in msg.args:
            markdown += self._message_field(arg) + "\n"
            for c in arg.consts:
                markdown += f'||| {"0x%0.2X" % c.value} - {c.name} ({c.description.get("russian", "")})|\n'

        return markdown

    def _generate_command(self, cmd):
        markdown = ""
        markdown += f"### Команда {self._nsp(cmd.name)} ({cmd.cid.upper()})\n\n"
        markdown += f"\n```c\n{self._func_head(cmd)}\n```\n"
        markdown += f'Код команды (CMD): `{cmd.cid}` или `{ascii_to_hex(cmd.cid)}`\n\n'
        markdown += f"**Запрос:** ({get_msg_len(cmd.request)} байт)\n\n"
        markdown += self._message_fields(cmd.request) + "\n"
        markdown += f"**Ответ:** ({get_msg_len(cmd.response)} байт)\n\n"
        markdown += self._message_fields(cmd.response) + "\n"
        markdown += "**Описание:**\n"
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
        archive.write(join(common_path, "Synch.png"), "Synch.png")
        archive.write(join(common_path, "crc.png"), "crc.png")
