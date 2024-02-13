__all__ = [
    "BUILDER_VERSION_MAJOR",
    "BUILDER_VERSION_MINOR",
    "BUILDER_VERSION_BUGFIX",
    "BUILDER_VERSION_SUFFIX",
    "BUILDER_VERSION",
    "XIBRIDGE_VERSION"
]

BUILDER_VERSION_MAJOR = 0
BUILDER_VERSION_MINOR = 11
BUILDER_VERSION_BUGFIX = 4

XIBRIDGE_VERSION_MAJOR = 1
XIBRIDGE_VERSION_MINOR = 1
XIBRIDGE_VERSION_BUGFIX = 1

BUILDER_VERSION_SUFFIX = ""

BUILDER_VERSION = "{}.{}.{}".format(BUILDER_VERSION_MAJOR, BUILDER_VERSION_MINOR, BUILDER_VERSION_BUGFIX)
if len(BUILDER_VERSION_SUFFIX) > 0:
    BUILDER_VERSION += "-{}".format(BUILDER_VERSION_SUFFIX)

XIBRIDGE_VERSION = "{}.{}.{}".format(XIBRIDGE_VERSION_MAJOR, XIBRIDGE_VERSION_MINOR, XIBRIDGE_VERSION_BUGFIX)
