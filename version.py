__all__ = [
    "BUILDER_VERSION_MAJOR",
    "BUILDER_VERSION_MINOR",
    "BUILDER_VERSION_BUGFIX",
    "BUILDER_VERSION_SUFFIX",
    "BUILDER_VERSION"
]

BUILDER_VERSION_MAJOR = 0
BUILDER_VERSION_MINOR = 10
BUILDER_VERSION_BUGFIX = 17

BUILDER_VERSION_SUFFIX = ""

BUILDER_VERSION = "{}.{}.{}".format(BUILDER_VERSION_MAJOR, BUILDER_VERSION_MINOR, BUILDER_VERSION_BUGFIX)
if len(BUILDER_VERSION_SUFFIX) > 0:
    BUILDER_VERSION += "-{}".format(BUILDER_VERSION_SUFFIX)
