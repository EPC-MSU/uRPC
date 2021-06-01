from io import TextIOWrapper

from collections import Counter


def _convert_protocol(xip):
    from functools import reduce
    from urpc import ast
    from urpc.storage.oldxi import ast as xiast

    def convert_description(langs):
        description = ast.AstNode.Description()
        for (code, text) in langs:
            description[code] = text
        return description

    def convert_argument(arg):
        descr = convert_description(arg.description)
        if isinstance(arg, xiast.NormalField):
            return ast.Argument(type=arg.type, name=arg.name, description=descr)
        elif isinstance(arg, xiast.FlagsetField):
            constants = [
                ast.FlagConstant(name=f.name, value=f.value, description=convert_description(f.description))
                for f in arg.flagset.members
            ]
            return ast.Argument(type=arg.type, name=arg.name, description=descr, consts=constants)
        elif isinstance(arg, xiast.ReservedField):
            # Assumed that reserved field can be only one in command fields
            return ast.Argument(type=ast.Array(ast.Integer8u, arg.size), name="reserved", description=descr)

    def convert_commands(accum, cmd):
        def convert_arguments(args):
            return [convert_argument(a) for a in args if not hasattr(a, "premod") or a.premod != "calb"]

        # assume that cid for all roles is the same
        cid = next(r.cid for r in cmd.roles)

        if len(cmd.roles) == 1 and cmd.roles[0].type == xiast.RoleType.universal:
            reader_descr = convert_description(cmd.description.reader)
            writer_descr = convert_description(cmd.description.writer)

            # getter
            g_request = ast.Message()
            g_response = ast.Message(args=convert_arguments(cmd.fields))
            accum.append(
                ast.Command(
                    cid="g" + cid,
                    name="get_" + cmd.name,
                    request=g_request,
                    response=g_response,
                    description=reader_descr
                )
            )

            # setter
            s_request = ast.Message(args=convert_arguments(cmd.fields))
            s_response = ast.Message()
            accum.append(ast.Command("s" + cid, "set_" + cmd.name, s_request, s_response, writer_descr))
        else:
            descr = convert_description(cmd.description.writer or cmd.description.reader)

            request, response = None, None
            if len(cmd.roles) == 1:
                if cmd.roles[0].type == xiast.RoleType.reader:
                    request = ast.Message()
                    response = ast.Message(args=convert_arguments(cmd.fields))
                elif cmd.roles[0].type == xiast.RoleType.writer:
                    request = ast.Message(args=convert_arguments(cmd.fields))
                    response = ast.Message(args=[])
            else:
                request = ast.Message(args=convert_arguments(cmd.fields))
                response = ast.Message(args=convert_arguments(cmd.answer))

            accum.append(ast.Command(cid=cid, name=cmd.name, request=request, response=response, description=descr))

        return accum

    return ast.Protocol(
        name="Imported project",
        version=xip.version,
        commands=reduce(convert_commands, xip.commands, [])
    )


class OldxiStorage:
    def __init__(self):
        pass

    def save(self, protocol, output):
        raise NotImplementedError

    def load(self, _input):
        from urpc.storage.oldxi.protocol import protocol

        text_input = TextIOWrapper(_input, encoding="utf-8")
        p = _convert_protocol(protocol.parseString(text_input.read())[0])

        dupe_names = set(name for name, n in Counter(cmd.name for cmd in p.commands).items() if n > 1)
        for cmd in p.commands:
            request, response = cmd.request, cmd.response
            if cmd.name not in dupe_names:
                continue

            if len(request.args):
                # this is setter
                cmd.name = "set_" + cmd.name
            elif len(response.args):
                # this is getter
                cmd.name = "get_" + cmd.name

        text_input.flush()
        text_input.detach()
        return p

    def init(self):
        #  Empty function for flake 8
        return None

# if __name__ == "__main__":
#     OldxiStorage().load("/home/vlad/test.xi")
