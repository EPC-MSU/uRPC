from os.path import abspath, dirname, join

from urpc.builder.firmware.common import build_firmware


def build_K1921BK01T_UART(project, output):
    build_firmware(project, output, join(abspath(dirname(__file__)), "resources"))
