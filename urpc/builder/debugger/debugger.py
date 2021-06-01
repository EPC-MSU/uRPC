from os.path import abspath, join, dirname
from zipfile import ZipFile, ZIP_DEFLATED
from mako.lookup import TemplateLookup
from urpc.builder.util import ClangView
from urpc.builder.util.resource import resources


_module_path = abspath(dirname(__file__))
_lookup = TemplateLookup((join(_module_path, "resources"),), input_encoding="utf-8", output_encoding="utf-8")


class DebuggerView(ClangView):

    def __init__(self, project):
        super().__init__(project)

        self._setters = []

        for acc in self._accessors:
            self._setters.append(acc[1])

    @property
    def argstructs(self):
        return self._argstructs

    def is_setter(self, cmd):
        return True if cmd in self._setters else False


def build(project, output):
    view = DebuggerView(project)
    utils = {
        "argstructs": view.argstructs,
        "library_shared_file": view.library_shared_file,
        "library_header_file": view.library_header_file
    }

    subdir_path = join(_module_path, "resources")
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for file in resources(subdir_path):
            archive_path = file[len(subdir_path) + 1:]
            if file.endswith(".mako"):
                # if "Project.cpp.mako" in file or "Project.h.mako" in file:
                archive.writestr(archive_path.replace(".mako", ""), _lookup.get_template(archive_path).render_unicode(
                    protocol=project,
                    is_namespaced=True,
                    view=view,
                    **utils
                ))
            else:
                archive.write(file, archive_path)
