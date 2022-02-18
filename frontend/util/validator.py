import re


version_pattern = re.compile(r"^((?:[1-9][0-9]*?)|0)(?:\.((?:[1-9][0-9]*?)|0))?(?:\.((?:[1-9][0-9]*?)|0))?$")
project_name_pattern = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*?$")


def check_if_empty(val, par_name="Value"):
    if not val.strip():
        raise ValueError("%s should not be empty string" % par_name)
    return val


def check_if_number(val, par_name="Value"):
    if not val.isdigit() and val.strip():
        raise ValueError("%s should be a number" % par_name)
    return val


def check_if_version(val, par_name="Version"):
    match = version_pattern.match(val)
    if not match:
        raise ValueError("{} should match pattern x.y.z, x.y or just x (e.g. '1.1.1', '1.1' or just '1')".format(
            par_name
        ))
    return val


def check_project_name(val, par_name="Project name"):
    match = project_name_pattern.match(val)
    if not match:
        raise ValueError("{} may contain only: letters [a-Z], digits [0-9], underscores; "
                         "but not starts with digits".format(par_name))
    return val
