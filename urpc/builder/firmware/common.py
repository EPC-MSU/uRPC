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
    join("croutine.c"): join("firmware", "src", "croutine.c"),
    join("croutine.h"): join("firmware", "inc", "croutine.h"),
    join("version.h.mako"): join("firmware", "inc", "version.h"),
    join("version_raw.h.mako"): join("firmware", "inc", "version_raw.h"),
    join("deprecated_definitions.h"): join("firmware", "inc", "deprecated_definitions.h"),
    join("event_groups.h"): join("firmware", "inc", "event_groups.h"),
    join("FreeRTOS.h"): join("firmware", "inc", "FreeRTOS.h"),
    join("heap_1.c"): join("firmware", "src", "heap_1.c"),
    join("list.c"): join("firmware", "src", "list.c"),
    join("list.h"): join("firmware", "inc", "list.h"),
    join("message_buffer.h"): join("firmware", "inc", "message_buffer.h"),
    join("mpu_prototypes.h"): join("firmware", "inc", "mpu_prototypes.h"),
    join("mpu_wrappers.h"): join("firmware", "inc", "mpu_wrappers.h"),
    join("pdc.h"): join("firmware", "inc", "pdc.h"),
    join("portable.h"): join("firmware", "inc", "portable.h"),
    join("portmacro.h"): join("firmware", "inc", "portmacro.h"),
    join("projdefs.h"): join("firmware", "inc", "projdefs.h"),
    join("queue.c"): join("firmware", "src", "queue.c"),
    join("queue.h"): join("firmware", "inc", "queue.h"),
    join("semphr.h"): join("firmware", "inc", "semphr.h"),
    join("stack_macros.h"): join("firmware", "inc", "stack_macros.h"),
    join("StackMacros.h"): join("firmware", "inc", "StackMacros.h"),
    join("stream_buffer.h"): join("firmware", "inc", "stream_buffer.h"),
    join("task.h"): join("firmware", "inc", "task.h"),
    join("tasks.c"): join("firmware", "src", "tasks.c"),
    join("timers.c"): join("firmware", "src", "timers.c"),
    join("timers.h"): join("firmware", "inc", "timers.h"),
    join("config.h.mako"): join("firmware", "inc", "config.h.mako")
}


def build_firmware(protocl, output, resources_path, path_mapping=common_path_mapping):
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for file in resources(resources_path):
            archive_path = file[len(resources_path) + 1:]
            assert not file.endswith(".mako")
            archive.write(file, archive_path)

        build_device(protocl, archive, path_mapping, is_namespaced=False)
