# import warnings
from os.path import join
from zipfile import ZipFile, ZIP_DEFLATED
from urpc.builder.device import build_device
from urpc.builder.util.resource import resources


common_path_mapping = {
    join("algorithm.c"): join("firmware", "src", "algorithm.c"),
    join("algorithm.h"): join("firmware", "inc", "algorithm.h"),
    join("commands.c.mako"): join("firmware", "src", "commands.c.mako"),
    join("commands.h.mako"): join("firmware", "inc", "commands.h.mako"),
    join("flowparser.c.mako"): join("firmware", "src", "flowparser.c.mako"),
    join("flowparser.h"): join("firmware", "inc", "flowparser.h"),
    join("handlers.c.mako"): join("firmware", "src", "handlers.c.mako"),
    join("handlers.h.mako"): join("firmware", "inc", "handlers.h.mako"),
    join("iobuffer.c"): join("firmware", "src", "iobuffer.c"),
    join("iobuffer.h"): join("firmware", "inc", "iobuffer.h"),
    join("macro.h"): join("firmware", "inc", "macro.h"),
    join("version.h.mako"): join("firmware", "inc", "version.h"),
    join("version_raw.h.mako"): join("firmware", "inc", "version_raw.h"),
}


def build_firmware(protocl, output, resources_path, path_mapping=common_path_mapping):
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for file in resources(resources_path):
            archive_path = file[len(resources_path) + 1:]
            assert not file.endswith(".mako")
            archive.write(file, archive_path)

        build_device(protocl, archive, path_mapping, is_namespaced=False)
