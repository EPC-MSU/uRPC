from pyparsing import Regex, Suppress, Or, ZeroOrMore
from urpc.storage.oldxi import ast


identifier = Regex("[A-Za-z][A-Za-z0-9_-]*")


def _build_attribute_list():
    def normalize(s, loc, toks):
        attr = toks[0]
        return ast.Attribute[attr]

    attr = Or(a.name for a in ast.Attribute).setParseAction(normalize)
    return attr + ZeroOrMore(Suppress(",") + attr)


_attribute_list = _build_attribute_list()

include_attributes = (Suppress("with") + _attribute_list).setResultsName("include")
exclude_attributes = (Suppress("without") + _attribute_list).setResultsName("exclude")
