<%namespace import="namespaced" module = "urpc.builder.device.utils.namespaced" inheritable="True"/>
<%
    from urpc import ast
    from urpc.util.cconv import ascii_to_hex, get_msg_len, type_to_cstr
%>\
% for cmd in protocol.commands:
h3. Команда ${cmd.name} (${cmd.cid.upper()})

<pre><code>result_t ${namespaced(cmd.name)}(device_t id${inout(cmd.request, 'input')}${inout(cmd.response, 'output')})</code></pre>Код команды (CMD): "${cmd.cid}" Или ${ascii_to_hex(cmd.cid)}.

*Запрос:* (${size_text(cmd.request)})
${message_fields(cmd.request)}
*Ответ:* (${size_text(cmd.response)})
${message_fields(cmd.response)}
*Описание:*
${cmd.description.get("russian", "")}
% endfor
<%def name="size_text(msg)">${ get_msg_len(msg) } байт</%def>\
<%def name="inout(msg, argname)">${', '+namespaced(argstructs[msg].name)+'* '+argname if len(argstructs[msg].fields) else ''}</%def>\
<%def name="message_fields(msg)">
    |${ "".join(type_to_cstr(ast.Integer32u)) }|CMD|Команда|
    % for arg in msg.args:
        % if arg.name == "reserved":
            |${ type_to_cstr(ast.Integer8u)[0] }|Reserved [${len(arg.type)}]|Зарезервировано (${len(arg.type)} байт)|
        % else:
            ${message_field(arg)}
        % endif
        % for c in arg.consts:
            |\2.| ${"0x%0.2X" % c.value} - ${c.name} (${c.description.get("russian", "")})|
        % endfor
    % endfor
    % if len(msg.args) > 0:
        |${ "".join(type_to_cstr(ast.Integer16u)) }|CRC|Контрольная сумма|
    % endif
</%def>\
<%def name="message_field(arg)"><%
                                    base_type, length = type_to_cstr(arg.type)
                                    c_str = "|"+base_type
                                    c_str += "|{} ".format(arg.name)
                                    c_str += length
                                    c_str += "|"+arg.description.get("russian", "")+"|"
%>${c_str}</%def>

h3. Об этом документе

Версия генератора документации: ${BUILDER_VERSION}.
