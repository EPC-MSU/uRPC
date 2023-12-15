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
        c_str = "|" + base_type
        c_str += "|{} ".format(arg.name)
        c_str += length
        c_str += "|" + ("Зарезервировано" if "reserved" in arg.name else arg.description.get("russian", "")) + "|"
        return c_str

    def _message_fields(self, msg):
        textile = ""
        textile += f'|_. {"".join(type_to_cstr(ast.Integer32u)) }|_. CMD|_. Команда|\n'
        for arg in msg.args:
            textile += self._message_field(arg) + "\n"
            for c in arg.consts:
                textile += f'||| {"0x%0.2X" % c.value} - {c.name} ({c.description.get("russian", "")})|\n'

        return textile

    def _generate_command(self, cmd):
        textile = ""
        textile += f"h3. Команда {self._nsp(cmd.name)} ({cmd.cid.upper()})\n\n"
        textile += f"<pre>{self._func_head(cmd)}</pre> "
        textile += f'Код команды (CMD): "{cmd.cid}" или {ascii_to_hex(cmd.cid)}\n\n'
        textile += f"*Запрос:* ({get_msg_len(cmd.request)} байт)\n\n"
        textile += self._message_fields(cmd.request) + "\n"
        textile += f"*Ответ:* ({get_msg_len(cmd.response)} байт)\n\n"
        textile += self._message_fields(cmd.response) + "\n"
        textile += "*Описание:*\n"
        textile += cmd.description.get("russian", "") + "\n"
        return textile

    def generate_textile(self):
        textile = get_static_part() + "\n"
        for cmd in self._commands:
            textile += self._generate_command(cmd) + "\n"
        if self.__getters != [] and self.__setters != []:
            for cmd in self.__getters:
                textile += self._generate_command(cmd) + "\n"
            for cmd in self.__setters:
                textile += self._generate_command(cmd) + "\n"
        textile += "\nВерсия генератора " + BUILDER_VERSION
        return textile


def build(project, output, lang):
    view = _MarkdownBuilderImpl(project)

    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "{}.md".format(project.name.lower()),
            view.generate_textile()
        )
        archive.write(join(common_path, "Synch.png"), "Synch.png")
        archive.write(join(common_path, "crc.png"), "crc.png")
