import re


version_pattern = re.compile(r"^((?:[1-9][0-9]*?)|0)(?:\.((?:[1-9][0-9]*?)|0))?(?:\.((?:[1-9][0-9]*?)|0))?$")
project_name_pattern = re.compile(r"^[a-z_][a-z0-9_]*?$")
product_name_pattern = re.compile(r"^.{1,40}$")
device_name_pattern = re.compile(
    r"^[a-zA-Z]"
    r"[a-zA-Z\ \!\"\#\$\%\&\'\(\)\*\+\,\-\.\/0-9\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]{1,38}"
    r"[a-zA-Z\!\"\#\$\%\&\'\(\)\*\+\,\-\.\/0-9\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]$")
manufacturer_name_pattern = re.compile(r"^.{1,16}$")
pid_vid_pattern = re.compile(r"^0[xX][0-9a-fA-F]{4}$")
command_name_pattern = re.compile(r"^[a-z_]*[a-z0-9_]*[a-z0-9]*?$")
arqument_name_pattern = re.compile(r"^[a-zA-Z][A-Za-z0-9]*?$")
constant_name_pattern = re.compile(r"^[A-Z]*[A-Z0-9_]*[A-Z0-9]*?$")


def validator_wrapper(func):
    """Wraps func into try-except block and return exception string if exception occured.
    Else wrapper returns empty string.

    :param func: function to wrap
    """
    def wrapper(val, par_name=None):
        try:
            func(val, par_name) if par_name is not None else func(val)
        except ValueError as exc:
            return str(exc) + " "
        return ""
    return wrapper


def check_if_empty(val, par_name="Value"):
    if not val.strip():
        raise ValueError("%s should not be empty string" % par_name)
    return val


def check_if_number(val, par_name="Value"):
    if not val.isdigit() and val.strip():
        raise ValueError("%s should be a number" % par_name)
    return val


@validator_wrapper
def check_if_version(val, par_name="Version"):
    match = version_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field must match the pattern "v.v.v", "v.v" or just "v" \
                         (for example, "1.2.3", "1.2" or just "1"). \
                         The "{}" field cannot contain letters and spaces.'.format(par_name, par_name))
    return val


@validator_wrapper
def check_project_name(val, par_name="Project name"):
    match = project_name_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field can only contain: lowercase letters [a-z], numbers [0-9] \
                          and underscores. The "{}" field cannot start with numbers and cannot \
                          contain spaces.'.format(par_name, par_name))
    return val


@validator_wrapper
def check_product_name(val, par_name="Product name"):
    match = product_name_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field cannot be longer than 40 symbols'
                         " and must contain at least 1 symbol.".format(par_name))
    return val


@validator_wrapper
def check_device_name(val, par_name="Device name"):
    match = device_name_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field cannot be longer than 40 symbols'
                         " and must contain at least 1 symbol.".format(par_name))
    return val


@validator_wrapper
def check_manufacturer(val, par_name="Manufacturer"):
    match = manufacturer_name_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field cannot be longer than 16 symbols'
                         " and must contain at least 1 symbol.".format(par_name))
    return val


@validator_wrapper
def check_pid(val, par_name="Product ID (PID)"):
    match = pid_vid_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field must be a 4-digit hex-number. For example, 0x1234.'.format(par_name))
    return val


@validator_wrapper
def check_vid(val, par_name="Vendor ID (VID)"):
    match = pid_vid_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field must be a 4-digit hex-number. For example, 0x1234.'.format(par_name))
    return val


def check_command_name(val, par_name="Command name"):
    match = command_name_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field should be in snake_case and can only contain: \
                          lowercase letters [a-z], numbers [0-9] and underscores. \
                          The "{}" field cannot start with numbers and cannot contain spaces.'.format(par_name, par_name
                                                                                                      ))
    return val


def check_argument_name(val, par_name="Argument name"):
    match = arqument_name_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field should be in CamelCase and only contain: \
                          lowercase letters [a-z], uppercase letters [A-Z] and numbers [0-9]. \
                          The "{}" can only starts with uppercase letters [A-Z] and cannot contain spaces.'.format(
            par_name, par_name))
    return val


def check_constant_name(val, par_name="Constant name"):
    match = constant_name_pattern.match(val)
    if not match:
        raise ValueError('The "{}" field should be in SCREAMING_SNAKE_CASE and can only contain: \
                          uppercase letters [A-Z], numbers [0-9] and underscores. \
                          The "{}" cannot stars with numbers or contain spaces.'.format(par_name, par_name))
    return val
