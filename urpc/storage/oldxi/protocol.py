from itertools import chain
from pyparsing import Suppress, OneOrMore, ZeroOrMore, Regex, Optional
from urpc.storage.oldxi import ast
from urpc.storage.oldxi.command import command
from urpc.storage.oldxi.flagset import flagset
from urpc.storage.oldxi.common import include_attributes, exclude_attributes


def _build_protocol():
    def normalize(s, loc, toks):
        p = ast.Protocol(
            toks["version"],
            ast.AttributeSet(
                toks["exclude"],
                toks["include"]
            ),
            toks["flagsets"],
            toks["commands"]
        )

        # FIXME: This is inefficient.
        # A much better approach is to collect all entities with unset references during parsing
        flagset_by_name = {fs.name: fs for fs in p.flagsets}

        for cmd in p.commands:
            for arg in (a for a in chain(cmd.fields, cmd.answer) if isinstance(a, ast.FlagsetField)):
                # Replace name with reference
                arg.flagset = flagset_by_name[arg.flagset]

        return p

    version = Suppress("protocol \"v") + Regex(r"(\d*[.])?\d+").setResultsName("version") + Suppress("\"")
    include = Optional(Suppress("defaults") + include_attributes, []).setResultsName("include")
    exclude = Optional(Suppress("defaults") + exclude_attributes, []).setResultsName("exclude")

    flagsets = ZeroOrMore(flagset).setResultsName("flagsets")
    commands = OneOrMore(command).setResultsName("commands")

    protocol = version + include + exclude + flagsets + commands
    return protocol.setParseAction(normalize)


_protocol = _build_protocol()


protocol = _protocol
