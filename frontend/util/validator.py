import re


version_pattern = re.compile(r"^((?:[1-9][0-9]*?)|0)(?:\.((?:[1-9][0-9]*?)|0))?(?:\.((?:[1-9][0-9]*?)|0))?$")
project_name_pattern = re.compile(r"^[a-z_][a-z0-9_]*?$")


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
        raise ValueError("The \"{}\" field must match the pattern \"v.v.v\", \"v.v\" or just \"v\" \
                         (for example, \"1.2.3\", \"1.2\" or just \"1\"). \
                         The \"{}\" field cannot contain letters and spaces.".format(
            par_name,
            par_name
        ))
    return val


def check_project_name(val, par_name="Project name"):
    match = project_name_pattern.match(val)
    if not match:
        raise ValueError("The \"{}\" field can only contain: lowercase letters [a-z], numbers [0-9] and underscores. \
                          The \"{}\" field cannot start with numbers and cannot contain spaces.".format(
            par_name,
            par_name
        ))
    return val
