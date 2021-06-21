<%namespace import="namespaced" module = "urpc.builder.device.utils.namespaced" inheritable="True"/>\
<%def name = "get_struct_type(cmd_r)">${namespaced(view._argstructs[cmd_r].name)}</%def>\
<%def name = "get_struct_code(cmd)">${view._struct_code(cmd.cid)}</%def>\
<%def name = "get_struct_code_ac(cmd)">${view._struct_code(cmd.cid[1:])}</%def>\
<%def name = "create_regular_handler(cmd)">\
    %if len(cmd.response.args) !=0:
void on_${namespaced(cmd.name)}(${get_struct_type(cmd.request)} *input, ${get_struct_type(cmd.response)} *output)\
    %else:
void on_${namespaced(cmd.name)}(${get_struct_type(cmd.request)} *input)\
    %endif
</%def>\
<%def name = "create_noinput_handler(cmd)">\
    %if len(cmd.response.args) != 0:
void on_${namespaced(cmd.name)}(${get_struct_type(cmd.response)} *output)\
    %else:
void on_${namespaced(cmd.name)}(void)\
    %endif
</%def>\
<%def name = "create_setter_handler(cmd)">\
void on_${namespaced(cmd.name)}(${get_struct_type(cmd.request)} *input)\
</%def>\
#ifndef _HANDLERS_H
#define _HANDLERS_H

/*
 * Other includes here.
 */
#include "commands.h"

#if defined(__cplusplus)
extern "C"
{
#endif

/*
 * Regular commands with input data must be below.
 */
%for cmd in view.regular_handlers_commands:
${create_regular_handler(cmd)};
%endfor

/*
 * Regular commands without input data must be below.
 */
%for cmd in view.noinput_handlers_commands:
${create_noinput_handler(cmd)};
%endfor

/*
 * Accessors like S*** handlers must be below.
 */
%for cmd in view.setter_handlers_commands:
${create_setter_handler(cmd)};
%endfor

#if defined(__cplusplus)
};
#endif

#endif  // _HANDLERS_H
