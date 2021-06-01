from urpc.builder.util.clang import namespace_symbol


def namespaced(context, string):
    if context["is_namespaced"]:
        protocol = context["protocol"]
        return getattr(namespace_symbol(protocol, string), "upper" if string.upper() == string else "lower")()
    else:
        return string
