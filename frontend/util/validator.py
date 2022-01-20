import re


version_pattern = re.compile(r"^((?:[1-9][0-9]*?)|0)(?:\.((?:[1-9][0-9]*?)|0))?(?:\.((?:[1-9][0-9]*?)|0))?$")


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
