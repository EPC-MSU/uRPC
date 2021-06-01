from os import sep
from os.path import join, abspath, dirname
from io import TextIOWrapper
from mako.runtime import Context
from mako.lookup import TemplateLookup
from urpc.util.accessor import split_by_type
from urpc.util.cconv import build_argstructs

from version import BUILDER_VERSION

_module_path = abspath(dirname(__file__))
_lookup = TemplateLookup((join(_module_path, "templates"),), input_encoding="utf-8", output_encoding="utf-8")


def build(project, output, lang):
    commands, accessors = map(list, split_by_type(project.commands))
    argstructs = build_argstructs(commands, accessors)

    text_output = TextIOWrapper(output, encoding="utf-8")
    template = _lookup.get_template(join(sep, "base.textile.mako"))
    ctx = Context(
        text_output,
        protocol=project,
        argstructs=argstructs,
        is_namespaced=True,
        BUILDER_VERSION=BUILDER_VERSION
    )
    template.render_context(ctx)
    text_output.detach()
