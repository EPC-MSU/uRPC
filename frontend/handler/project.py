import os
from io import BytesIO

from tornado.httputil import url_concat
from tornado.web import HTTPError

from frontend.handler.base import BaseRequestHandler
from urpc.builder import bindings
from urpc.builder import firmware
from urpc.builder.adapters import tango
from urpc.builder.debugger import debugger
from urpc.builder.device import device
from urpc.builder.documentation.textile import textile
from urpc.builder.documentation.sphinx import sphinx
from urpc.builder.library import clib
from urpc.builder.profiles import profiles
from urpc.storage import JsonStorage, OldxiStorage


def _normalize_protocol_name(protocol):
    return "{}_{}".format(protocol.name, protocol.version)


def _normalize_target_name(protocol, target, subtarget=None):
    target_name = "{}_{}".format(_normalize_protocol_name(protocol), target.lower())
    return "{}({})".format(target_name, subtarget) if subtarget else target_name


class ProjectHandler(BaseRequestHandler):
    def __init__(self, application, request, sessions, **kwargs):
        super().__init__(application, request, **kwargs)

        self._sessions = sessions

        self._json_storage = JsonStorage()
        self._oldxi_storage = OldxiStorage()

    def _generate_firmware(self, protocol, output_buffer):
        device_type = self.get_query_argument("device")
        file_name = "{}.zip".format(_normalize_target_name(protocol, "firmware", device_type))

        if device_type == "K1921BK01T":
            firmware.build_K1921BK01T(protocol, output_buffer)
        elif device_type == "K1921BK01T-UART":
            firmware.build_K1921BK01T_UART(protocol, output_buffer)
        elif device_type == "K1986BE92QI":
            firmware.build_K1986BE92QI(protocol, output_buffer)
        elif device_type == "K1986BE92QI-UART":
            firmware.build_K1986BE92QI_UART(protocol, output_buffer)
        elif device_type == "TM4C1294KCPDT":
            firmware.build_TM4C1294KCPDT(protocol, output_buffer)
        elif device_type == "LM3S5R31":
            firmware.build_LM3S5R31(protocol, output_buffer)
        elif device_type == "STM32F103C6-UART":
            firmware.build_STM32F103C6_UART(protocol, output_buffer)
        else:
            raise ValueError("Unknown firmware generation ")

        mime = "application/zip"
        return file_name, mime

    def _generate_doc(self, protocol, output_buffer):
        doc_format = self.get_query_argument("format")

        if doc_format == "Textile":
            textile.build(protocol, output_buffer, "ru")
            file_name = "{}.zip".format(_normalize_target_name(protocol, "wiki"))
            mime = "application/zip"
        elif doc_format == "Sphinx":
            sphinx.build(protocol, output_buffer)
            file_name = "{}.zip".format(_normalize_target_name(protocol, "sphinx"))
            mime = "application/zip"
        else:
            raise ValueError("Unknown documentation generation")
        return file_name, mime

    def _generate_bind(self, protocol, output_buffer):
        lang_name = self.get_query_argument("format", "").lower()

        if lang_name == "python":
            bindings.python.build(protocol, output_buffer)
        elif lang_name == "c#":
            bindings.csharp.build(protocol, output_buffer)
        else:
            raise ValueError("Unknown bindings generation request")
        file_name = "{}.zip".format(_normalize_target_name(protocol, "bindings", lang_name))
        mime = "application/zip"
        return file_name, mime

    def get(self, action):
        protocol = self._sessions[self.current_user]

        output_buffer, file_name, mime = BytesIO(), "", ""
        if action == "save":
            self._json_storage.save(protocol, output_buffer)
            file_name = "{}.json".format(_normalize_protocol_name(protocol))
            mime = "application/json"

        elif action == "generate_firmware":
            file_name, mime = self._generate_firmware(protocol, output_buffer)
        elif action == "generate_documentation":
            file_name, mime = self._generate_doc(protocol, output_buffer)
        elif action == "generate_library":
            clib.build(protocol, output_buffer)
            file_name = "{}.zip".format(_normalize_target_name(protocol, "client"))
            mime = "application/zip"

        elif action == "generate_abstract_device":
            is_namespaced = self.get_query_argument("is_namespaced", "False") == "True"

            device.build_full(protocol, output_buffer, is_namespaced=is_namespaced)
            if is_namespaced:
                file_name = "{}.zip".format(_normalize_target_name(protocol, "abstract_device"))
            else:
                file_name = "{}.zip".format(_normalize_target_name(protocol, "abstract_device_firmware"))
            mime = "application/zip"

        elif action == "generate_tango":
            tango.build(protocol, output_buffer)
            file_name = "{}.zip".format(_normalize_target_name(protocol, "tango"))
            mime = "application/zip"

        elif action == "generate_debugger":
            debugger.build(protocol, output_buffer)
            file_name = "{}.zip".format(_normalize_target_name(protocol, "debugger"))
            mime = "application/zip"

        elif action == "generate_bindings":
            file_name, mime = self._generate_bind(protocol, output_buffer)
        else:
            raise HTTPError(404)

        output_buffer.seek(0)

        while True:
            data = output_buffer.read(16384)
            if not data:
                break
            self.write(data)

        self.set_header("Content-Type", mime)
        self.set_header("Content-Disposition", 'attachment; filename="' + file_name + '"')

    def post(self, action):
        if action == "load":
            if not self.request.files or len(self.request.files) == 0:  # if user hasn"t recently loaded project file
                self.redirect(".." + self.reverse_url("main"))
            file_info = self.request.files["project"][0]
            ext = os.path.splitext(file_info["filename"])[1]

            content = BytesIO(file_info["body"])
            protocol = (self._json_storage if ext == ".json" else self._oldxi_storage).load(content)

            self._sessions[self.current_user] = protocol

            self.redirect(url_concat(self.reverse_url("editor"), {"action": "view", "handle": protocol.uid}))

        elif action == "assembly_profiles":
            protocol = self._sessions[self.current_user]

            output_buffer, file_name, mime = BytesIO(), "", ""

            files_info = self.request.files["profiles"]

            profiles_list = []

            for profile in files_info:
                profiles_list.append((profile["filename"], profile["body"]))

            profiles.build(protocol, profiles_list, output_buffer, is_namespaced=True)

            file_name = "{}.zip".format(_normalize_target_name(protocol, "profiles"))
            mime = "application/zip"

            output_buffer.seek(0)

            while True:
                data = output_buffer.read(16384)
                if not data:
                    break
                self.write(data)

            self.set_header("Content-Type", mime)
            self.set_header("Content-Disposition", 'attachment; filename="' + file_name + '"')

        else:
            raise HTTPError(404)
