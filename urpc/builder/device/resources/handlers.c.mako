<%namespace file="handlers.h.mako" import="get_struct_type, create_noinput_handler"></%namespace>\
<%namespace file="handlers.h.mako" import="create_regular_handler"></%namespace>\
<%namespace file="handlers.h.mako" import="create_setter_handler"></%namespace>\
<%namespace import="namespaced" module = "urpc.builder.device.utils.namespaced" inheritable="True"/>\
/*
 * Each file must start with this include.
 * File containes global settings.
 */
#include "settings.h"

/*
 * Main includes here.
 */
#include "handlers.h"

/*
 * This file is autogenerated.
 * Changes made to this file can be overwritten.
 */

#if defined(__cplusplus)
extern "C"
{
#endif

/*
 * Regular commands with input data must be below (maybe with output).
 */
%for cmd in view.regular_handlers_commands:
${create_regular_handler(cmd)}
{

}

%endfor
/*
 * Regular commands without input data must be below (maybe with output).
 */
%for cmd in view.noinput_handlers_commands:
${create_noinput_handler(cmd)}
{

}

%endfor
/*
 * Accessors like S*** handlers must be below.
 */
%for cmd in view.setter_handlers_commands:
${create_setter_handler(cmd)}
{

}

%endfor\

#if defined(__cplusplus)
};
#endif
