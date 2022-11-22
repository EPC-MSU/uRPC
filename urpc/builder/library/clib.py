from os.path import abspath, join as join_path, dirname, commonprefix
from textwrap import indent, dedent
from zipfile import ZipFile, ZIP_DEFLATED

from urpc.ast import Message, ArrayType, FloatType, IntegerType
from urpc.builder.util import ClangView
from urpc.builder.util.clang import namespace_symbol
from urpc.builder.util.resource import resources
from urpc.util.cconv import type_to_cstr
from version import BUILDER_VERSION_MAJOR, BUILDER_VERSION_MINOR, BUILDER_VERSION_BUGFIX, BUILDER_VERSION_SUFFIX, \
    BUILDER_VERSION


def _get_msg_buffer_size(msg):
    assert isinstance(msg, Message)
    return sum(a.type_.size for a in msg.args)


def _get_accessor_name(getter_or_setter_cmd):
    return getter_or_setter_cmd.name[4:]


class _Function:
    in_arg_name = "input"
    out_arg_name = "output"

    def __init__(self, cmd, argstructs):
        self._cmd = cmd

        self._argstructs = argstructs

    @property
    def name(self):
        return self._cmd.name

    @property
    def cid(self):
        return self._cmd.cid

    @property
    def description(self):
        return self._cmd.description

    # FIXME: this three functions are awful hacks!! Kill it with fire!
    @property
    def request(self):
        return self._cmd.request

    @property
    def response(self):
        return self._cmd.response


class _ClibBuilderImpl(ClangView):
    def __init__(self, protocol):
        super().__init__(protocol)
        self.__protocol = protocol

        if len(self._accessors) == 0:
            self.__getters, self.__setters = [], []
        else:
            self.__getters, self.__setters = zip(*self._accessors)

    @property
    def __functions(self):
        for cmd in self._commands:
            yield _Function(cmd, self._argstructs)
        for (getter, setter) in self._accessors:
            yield _Function(getter, self._argstructs)
            yield _Function(setter, self._argstructs)

    def __generate_flagset(self, flagset):
        result = ""

        for name, value, description in flagset.members:
            flagset_name = namespace_symbol(self.__protocol, name).upper()
            result += dedent("#define {name}    {value} /**< \\~english {english} \\~russian {russian} */".format(
                name=flagset_name,
                value=value,
                english=description["english"],
                russian=description["russian"]
            ) + "\n")

        return result

    def __generate_argstruct(self, argstruct):
        result = dedent("""\
        typedef struct
        {
        """)
        for decl, description in argstruct.members:
            result += indent("{decl}; /**< \\~english {english} \\~russian {russian} */".format(
                decl=decl,
                **description
            ), "    ") + "\n"
        result += "\n} " + namespace_symbol(self.__protocol, argstruct.name) + ";\n"
        return result

    def __generate_function(self, return_type_name, func_name, args_list_str, body=None):
        signature = ""
        if not body:
            signature += self.__get_export_macro_name() + " "
        signature += return_type_name + " "
        if not body:
            signature += self.__get_calling_convention_macro_name() + " "
        signature += "{}({})".format(func_name, args_list_str)
        return signature + (";" if body is None else "\n{\n" + indent(body.strip(), "    ") + "\n}") + "\n"

    def __generate_data_move_statement(self, buffer_name, arg, generate_move_impl):
        base_type, length = type_to_cstr(arg.type_)
        field_access = "{}->{}".format(buffer_name, arg.name)
        if length:
            result = "for(i=0; i<{}; i++) {}".format(
                len(arg.type_), generate_move_impl(base_type, field_access + "[i]")
            )
        else:
            result = generate_move_impl(base_type, field_access)
        result += ";"
        return result

    def __generate_put_into_buffer_statement(self, base_type, field_access):
        return "push_{}(&p, {})".format(base_type, field_access)

    def __generate_get_from_buffer_statement(self, base_type, field_access):
        return "{} = pop_{}(&p)".format(field_access, base_type)

    def __need_loop(self, func):
        for arg in func.request.children:
            _, length = type_to_cstr(arg.type_)
            if length != "":
                return True
        for arg in func.response.children:
            _, length = type_to_cstr(arg.type_)
            if length != "":
                return True
        return False

    def __generate_command_function_body(self, func):
        has_input, has_output = bool(len(func.request.children)), bool(len(func.response.children))

        request_size, response_size = _get_msg_buffer_size(func.request), _get_msg_buffer_size(func.response)

        def __generate_call_expression():
            result = 'urpc_device_send_request(device, "{cid}"'.format(cid=func.cid)
            result += ", in_buffer, {}".format(request_size) if has_input else ", NULL, 0"
            result += ", out_buffer, {}".format(response_size) if has_output else ", NULL, 0"
            result += ")"
            return result

        body = ""
        if has_input or has_output:
            body += dedent("""\
            uint8_t *p;
            """)

            if self.__need_loop(func):
                body += dedent("""\
                unsigned int i;
                """)

        if has_input:
            body += dedent("""\
            uint8_t in_buffer[{size}];
            memset(in_buffer, 0, {size});
            """.format(size=request_size))

        if has_output:
            body += dedent("""\
            uint8_t out_buffer[{size}];
            memset(out_buffer, 0, {size});
            """.format(size=response_size))

        body += dedent("""\
        urpc_device_handle_t device;
        if(handle < 0)
        {
            return result_error;
        }
        {
            std::lock_guard<std::mutex> lock(impl_by_handle_mutex);
            try
            {
                device = impl_by_handle.at(handle);
            }
            catch(const std::out_of_range &)
            {
                return result_error;
            }
        }
        """)
        if has_input:
            body += "p = in_buffer;\n"
            for index, arg in enumerate(func.request.children):
                body += self.__generate_data_move_statement(
                    func.in_arg_name, arg, self.__generate_put_into_buffer_statement
                ) + "\n"
        call_expression = __generate_call_expression()
        body += "urpc_result_t res;\n"
        body += "if((res = {}) != urpc_result_ok)".format(call_expression) + dedent("""
        {
            result_t new_res;
            switch (res)
            {
            case urpc_result_ok:
                 new_res = result_ok;
                 break;
            case urpc_result_error:
                 new_res = result_error;
                 break;
            case urpc_result_value_error:
                 new_res = result_value_error;
                 break;
            case urpc_result_nodevice:
                 new_res = result_nodevice;
                 break;
            case urpc_result_timeout:
                 new_res = result_timeout;
                 break;
            default:
                 new_res = res;
                 break;
            }
            return new_res;
        }
        """)
        if has_output:
            body += "p = out_buffer;\n"
            for index, arg in enumerate(func.response.children):
                body += self.__generate_data_move_statement(
                    func.out_arg_name, arg, self.__generate_get_from_buffer_statement
                ) + "\n"
        body += "return result_ok;"
        return dedent(body)

    def __generate_command_func(self, func, signature_only=False):
        return_type_name = "result_t"
        func_name = namespace_symbol(self.__protocol, func.name)

        def func_arg_str(name, msg):
            if len(msg.children) == 0:
                return ""
            argstruct = self._argstructs[msg]
            return ", {} *{}".format(namespace_symbol(self.__protocol, argstruct.name), name)

        def arg_descr_str(is_req, language):
            argument_descriptions = {
                "in": {"russian": "Данные, отправляемые устройству.", "english": "Device in data."},
                "out": {"russian": "Данные, получаемые с устройства.", "english": "Device out data."}
            }
            msg = func.request if is_req else func.response
            direction = "in" if is_req else "out"
            var_name = "input" if is_req else "output"
            if len(msg.children) == 0:
                return ""
            return f"@param[{direction}] {var_name} - {argument_descriptions[direction][language]}"

        def prepare_multiline_string(st):
            return st.replace("\n", "\n * ")

        descr = ""
        if signature_only:
            open_name = namespace_symbol(self.__protocol, "open_device")
            descr = dedent(f"""\
            /**
             * \\~english
             * {{en_descr}}
             * @param[in] handle - Device ID, obtained by {open_name}() function.
             * {arg_descr_str(True, 'english')}
             * {arg_descr_str(False, 'english')}
             * \\~russian
             * {{ru_descr}}
             * @param[in] handle - Идентификатор устройства, полученный от {open_name}().
             * {arg_descr_str(True, 'russian')}
             * {arg_descr_str(False, 'russian')}
             */\n""")
            descr = descr.format(ru_descr=prepare_multiline_string(func.description["russian"]),
                                 en_descr=prepare_multiline_string(func.description["english"]))
            descr = descr.replace(" * \n", "")

        return descr + self.__generate_function(
            return_type_name, func_name,
            "device_t handle" + func_arg_str("input", func.request) + func_arg_str("output", func.response),
            None if signature_only else self.__generate_command_function_body(func)
        )

    def __generate_open_func(self, signature_only=False):
        descr = ""
        if signature_only:
            descr = dedent("""\
            /**
             * \\~english
             * Open a device by name \\a name and return identifier of the device which can be used in calls.
             * @param[in] name - A device name.
             * Device name has form "com:port" or "xi-net://host/serial" or "udp://host:port".
             * In case of USB-COM port the "port" is the OS device uri.
             * For example "com:\\\\.\\COM3" in Windows or "com:///dev/ttyACM34" in Linux/Mac.
             * In case of network device the "host" is an IPv4 address or fully qualified domain uri (FQDN),
             * "serial" is the device serial number in hexadecimal system.
             * For example "xi-net://192.168.0.1/00001234" or "xi-net://hostname.com/89ABCDEF".
             * In case of ethernet udp-com adapter the "host" is an IPv4 address, "port" is network port
             * For example: "udp://192.168.0.2:1024"
             * Note: only one program may use COM-device in same time.
             * If errors occur when opening device, you need to make sure that the COM port is in the system and
             * device is not currently used by other programs.
             * \\~russian
             * Открывает устройство по имени \\a name и возвращает идентификатор устройства.
             * @param[in] name - Имя устройства.
             * Имя устройства имеет вид "com:port" или xi-net://host/serial или udp://host:port.
             * Для COM устройства "port" это имя устройства в ОС.
             * Например "com:\\\\.\\COM3" (Windows) или "com:///dev/tty/ttyACM34" (Linux/Mac).
             * Для сетевого (XiNet) устройства "host" это IPv4 адрес или полностью определённое имя домена,
             * "serial" это серийный номер устройства в шестнадцатеричной системе.
             * Например "xi-net://192.168.0.1/00001234" или "xi-net://hostname.com/89ABCDEF".
             * Для ethernet переходника com-udp "host" это IPv4 адрес переходника, "port" это порт переходника.
             * Например "udp://192.168.0.2:1024"
             * Замечание: в один момент времени COM устройство может использоваться только одной программой.
             * Если при открытии устройства возникают ошибки, нужно убедиться, что COM-порт есть в системе и что это
             * устройство в данный момент не используется другими программами
             */\n""")
        func_name = namespace_symbol(self.__protocol, "open_device")
        return descr + self.__generate_function(
            "device_t", func_name, "const char *uri",
            body=None if signature_only else dedent("""\
            device_t handle;
            urpc_device_handle_t device;
            device = urpc_device_create(uri);
            if(device == NULL) {
                return device_undefined;
            }
            {
                std::lock_guard<std::mutex> lock(impl_by_handle_mutex);
                do
                {
                    handle = rand();
                }
                while(impl_by_handle.count(handle) != 0);
                impl_by_handle[handle] = device;
            }
            return handle;
            """)
        )

    def __generate_lib_version_func(self, signature_only=False):
        func_name = namespace_symbol(self.__protocol, "libversion")
        descr = ""
        if signature_only:
            descr = dedent("""\
            /**
             * \\~english
             * Get library version.
             * @param[out] lib_version - Library version.
             * \\~russian
             * Версия библиотеки.
             * @param[out] lib_version - Версия библиотеки.
             */\n""")
        return descr + self.__generate_function(
            "result_t", func_name, "char *lib_version",
            body=None if signature_only else dedent("""\
            const char *lib_v = "{LIB_VERSION}";
            strcpy(lib_version,lib_v);
            return result_ok;
            """.format(LIB_VERSION=self.__protocol.version)
            )
        )

    def __generate_close_func(self, signature_only=False):
        descr = ""
        if signature_only:
            descr = dedent("""\
            /**
             * \\~english
             * Close specified device.
             * @param handle_ptr - An identifier of device.
             * \\~russian
             * Закрывает устройство.
             * @param handle_ptr - Идентификатор устройства.
             */\n""")
        func_name = namespace_symbol(self.__protocol, "close_device")
        return descr + self.__generate_function(
            "result_t", func_name, "device_t *handle_ptr",
            body=None if signature_only else dedent("""\
            if(handle_ptr == NULL)
            {
                return result_error;
            }
            device_t handle = *handle_ptr;
            if(handle < 0)
            {
                return result_error;
            }
            urpc_device_handle_t device;
            {
                std::lock_guard<std::mutex> lock(impl_by_handle_mutex);
                try
                {
                    device = impl_by_handle.at(handle);
                }
                catch(const std::out_of_range &)
                {
                    return result_error;
                }
                impl_by_handle.erase(handle);
            }
            if(urpc_device_destroy(&device) != urpc_result_ok)
            {
                return result_error;
            }
            return result_ok;
            """)
        )

    def __generate_logging_callback(self, callback_name, body=None):
        return_type_name = "void"
        callback_args = "int loglevel, const wchar_t *message, void *"
        return self.__generate_function(return_type_name, callback_name, callback_args, body)

    def __generate_wide_logging_callback(self, signature_only):
        return self.__generate_logging_callback(
            namespace_symbol(self.__protocol, "logging_callback_stderr_wide"),
            None if signature_only else dedent("""\
            if(loglevel > LOGLEVEL_WARNING) return;
            fwprintf(stderr, L"%ls\\n", message);
            """)
        )

    def __generate_narrow_logging_callback(self, signature_only):
        return self.__generate_logging_callback(
            namespace_symbol(self.__protocol, "logging_callback_stderr_narrow"),
            None if signature_only else dedent("""\
            if(loglevel > LOGLEVEL_WARNING) return;
            fprintf(stderr, "%ls\\n", message);
            """)
        )

    def __generate_logging_callback_setter(self, callback_type_name, signature_only):
        return_type_name = "void"
        func_name = namespace_symbol(self.__protocol, "set_logging_callback")
        func_args = "{} cb, void *data".format(callback_type_name)

        if signature_only:
            return self.__generate_function(return_type_name, func_name, func_args)
        else:
            return dedent("""\
            static wchar_t *str_to_widestr(const char *str)
            {
                wchar_t *result;
                mbstate_t mbs;
                size_t len;
                memset(&mbs, 0, sizeof(mbstate_t));
                len = mbsrtowcs(NULL, &str, 0, &mbs);
                if(len == (size_t)(-1))
                {
                    return NULL;
                }
                result = (wchar_t*)malloc(sizeof(wchar_t)*(len+1));
                if(result && mbsrtowcs(result, &str, len+1, &mbs) != len)
                {
                    free(result);
                    return NULL;
                }
                return result;
            }
            static void zf_log_out_dummy_callback(const zf_log_message *, void *) {}
            ZF_LOG_DEFINE_GLOBAL_OUTPUT = {0, 0, zf_log_out_dummy_callback};
            struct userimpl_data_t
            {
                void *payload;
                """ + callback_type_name + """ cb;
            };
            static std::mutex callback_setter_mutex;
            static void zf_log_out_userimpl_callback(const zf_log_message *msg, void *data)
            {
                userimpl_data_t impl;
                {
                    std::lock_guard<std::mutex> lock(callback_setter_mutex);
                    impl = *(userimpl_data_t *)data;
                }
                unsigned int log_level;
                switch(msg->lvl)
                {
                    case ZF_LOG_DEBUG:
                    case ZF_LOG_VERBOSE:
                        log_level = LOGLEVEL_DEBUG;
                        break;
                    case ZF_LOG_INFO:
                        log_level = LOGLEVEL_INFO;
                        break;
                    case ZF_LOG_WARN:
                        log_level = LOGLEVEL_WARNING;
                        break;
                    case ZF_LOG_ERROR:
                    case ZF_LOG_FATAL:
                        log_level = LOGLEVEL_ERROR;
                        break;
                    default:
                        return;
                }
                wchar_t *wmsg = str_to_widestr(msg->buf);
                impl.cb(log_level, wmsg, impl.payload);
                free(wmsg);
            }
            """) + self.__generate_function(return_type_name, func_name, func_args, body=dedent("""\
            std::lock_guard<std::mutex> lock(callback_setter_mutex);
            free(ZF_LOG_GLOBAL_OUTPUT->arg);
            if(cb != NULL)
            {
                userimpl_data_t *impl = (userimpl_data_t *)malloc(sizeof(userimpl_data_t));
                impl->cb = cb;
                impl->payload = data;
                zf_log_set_output_v(ZF_LOG_PUT_STD, (void *)impl, &zf_log_out_userimpl_callback);
            }
            else
            {
                zf_log_set_output_v(0, 0, zf_log_out_dummy_callback);
            }
            """))

    def __generate_logging_aspect(self, for_header_inclusion):
        library_name = self.__get_library_name()
        callback_type_name = namespace_symbol(self.__protocol, "logging_callback_t")

        if for_header_inclusion:
            return dedent("""\
            /**
             * \\~english
             * @name Logging level
             * \\~russian
             * @name Уровень логирования
             */
            //@{
            /**
             * \\~english
             * Logging level - error
             * \\~russian
             * Уровень логирования - ошибка
             */
            #define LOGLEVEL_ERROR         0x01
            /**
             * \\~english
             * Logging level - warning
             * \\~russian
             * Уровень логирования - предупреждение
             */
            #define LOGLEVEL_WARNING     0x02
            /**
             * \\~english
             * Logging level - info
             * \\~russian
             * Уровень логирования - информация
             */
            #define LOGLEVEL_INFO        0x03
            /**
             * \\~english
             * Logging level - debug
             * \\~russian
             * Уровень логирования - отладка
             */
            #define LOGLEVEL_DEBUG        0x04
            //@}
            """) + dedent("""
            /**
             * \\~english
             * Logging callback prototype.
             * @param loglevel - A logging level.
             * @param message - A message.
             * \\~russian
             * Прототип функции обратного вызова для логирования.
             * @param loglevel - Уровень логирования.
             * @param message - Сообщение.
             */
            typedef void ({calling_convention} *{type_name})(int loglevel, const wchar_t *message, void *user_data);
            """.format(
                calling_convention=self.__get_calling_convention_macro_name(),
                type_name=callback_type_name
            )) + dedent("""
            /**
             * \\~english
             * Simple callback for logging to stderr in wide chars.
             * @param loglevel - A logging level.
             * @param message - A message.
             * \\~russian
             * Простая функция логирования на stderr в широких символах.
             * @param loglevel - Уровень логирования.
             * @param message - Сообщение.
             */
            """ + self.__generate_wide_logging_callback(
                signature_only=True
            )) + dedent("""
            /**
             * \\~english
             * Simple callback for logging to stderr in narrow (single byte) chars.
             * @param loglevel - A logging level.
             * @param message - A message.
             * \\~russian
             * Простая функция логирования на stderr в узких (однобайтных) символах.
             * @param loglevel - Уровень логирования.
             * @param message - Сообщение.
             */
            """ + self.__generate_narrow_logging_callback(
                signature_only=True
            )) + dedent("""
            /**
             * \\~english
             * Sets a logging callback.
             * Passing NULL disables logging.
             * @param logging_callback a callback for log messages
             * \\~russian
             * Устанавливает функцию обратного вызова для логирования.
             * Передача NULL в качестве аргумента отключает логирование.
             * @param logging_callback указатель на функцию обратного вызова
             */
            """ + self.__generate_logging_callback_setter(callback_type_name, signature_only=True))
        else:
            return '#include "{}.h"\n'.format(library_name) + dedent("""\
            #include <cstring>
            #include <cstdlib>
            #include <mutex>

            #include <zf_log.h>
            """) + "\n".join((
                self.__generate_logging_callback_setter(callback_type_name, signature_only=False),
                self.__generate_wide_logging_callback(signature_only=False),
                self.__generate_narrow_logging_callback(signature_only=False)
            )) + "\n"

    def generate_logging_impl_file(self):
        return self.__generate_logging_aspect(for_header_inclusion=False)

    def __get_picojson_field_type(self, field_type):
        if isinstance(field_type, IntegerType):
            return "int64_t" if field_type.signed else "uint64_t"
        elif isinstance(field_type, FloatType):
            return "double"
        elif isinstance(field_type, ArrayType):
            return "picojson::array"
        else:
            raise TypeError("Unknown field type")

    def __generate_get_profile_func(self, signature_only):
        func_name = namespace_symbol(self.__protocol, "get_profile")

        def generate_arg_serializer(arg):
            field_name = arg.name

            if isinstance(arg.type_, ArrayType):
                picojson_type = self.__get_picojson_field_type(arg.type_.type_)

                return dedent("""\
                picojson::array field_output_json({length});
                for(unsigned int i = 0; i < {length}; i++)
                    field_output_json[i] = picojson::value(static_cast<{picojson_type}>(command_output.{field}[i]));
                command_output_json["{field}"] = picojson::value(field_output_json);
                """.format(field=field_name,
                           length=len(arg.type_),
                           picojson_type=picojson_type
                           ))
            else:
                picojson_type = self.__get_picojson_field_type(arg.type_)

                return dedent("""\
                command_output_json[\"{field}\"]= picojson::value(static_cast<{picojson_type}>(command_output.{field}));
                """.format(field=field_name,
                           picojson_type=picojson_type))

        def generate_command_serializer(cmd):
            accessor_name = _get_accessor_name(cmd)
            response_argstruct = self._argstructs[cmd.response]
            getter_func_name = namespace_symbol(self.__protocol, cmd.name)
            arg_type_name = namespace_symbol(self.__protocol, response_argstruct.name)

            body = dedent("""\
            {type} command_output;
            picojson::value::object command_output_json;
            if({getter}(handle, &command_output) != result_ok) result = result_error;
            """.format(
                getter=getter_func_name,
                type=arg_type_name,
            ))

            for arg in response_argstruct.args:
                body += "{\n" + indent(generate_arg_serializer(arg), "    ") + "}\n"

            body += dedent("""\
                profile_json["{field}"] = picojson::value(command_output_json);
                """.format(
                field=accessor_name
            ))
            return body

        body = None
        if not signature_only:
            body = dedent("""
            result_t result = result_ok;
            picojson::value::object profile_json;
            """)

            for cmd in self.__getters:
                body += "{\n" + indent(generate_command_serializer(cmd), "    ") + "}\n"

            body += dedent("""
            std::string out_str = picojson::value(profile_json).serialize(true);
            size_t size = out_str.size();
            (*buffer) = static_cast<char *>(allocate(size + 1));
            memcpy((*buffer), out_str.c_str(), size);
            (*buffer)[size] = '\\0';
            return result;
            """)

        return self.__generate_function(
            "result_t", func_name, "device_t handle, char **buffer, void *(*allocate)(size_t)", body
        )

    def __generate_set_profile_func(self, signature_only):
        result_var_name = "result"
        func_name = namespace_symbol(self.__protocol, "set_profile")

        def generate_tests_condition(tests, body):
            if_content = indent(body, "    ")
            else_content = indent("{result_var} = result_error;\n".format(
                result_var=result_var_name
            ), "    ")
            return "if(" + " && ".join(tests) + ") \n{\n" + if_content + "}\nelse\n{\n" + else_content + "}\n"

        def generate_array_field_deserializer(command_data_var_name, field_json_var_name, field_name, arg):
            assert isinstance(arg.type_, ArrayType)

            array_length = len(arg.type_)
            length_test = "{field_json_var}.size() == {length}".format(
                field_json_var=field_json_var_name,
                length=array_length
            )

            picojson_type = self.__get_picojson_field_type(arg.type_.type_)
            element_check_type_impl = "[](picojson::value const &e) { return e.is<" + picojson_type + ">(); }"
            element_types_test = "std::all_of({field_json_var}.cbegin(), {field_json_var}.cend(), {check_impl})".format(
                field_json_var=field_json_var_name,
                check_impl=element_check_type_impl
            )

            c_type, _ = type_to_cstr(arg.type_)
            body = dedent("""\
            unsigned int i;
            for(i=0; i < {}; i++) """.format(array_length)) + "{" + indent(dedent("""
                {command_data_var}.{field_name}[i] = static_cast<{c_type}>({field_json_var}[i].get<{picojson_type}>());
            """.format(
                command_data_var=command_data_var_name,
                field_name=field_name,
                field_json_var=field_json_var_name,
                c_type=c_type,
                picojson_type=picojson_type,
            )), "    ") + "}\n"

            tests = (
                length_test,
                element_types_test
            )
            return generate_tests_condition(tests, body)

        def generate_scalar_field_deserializer(command_data_var_name, field_json_var_name, field_name, arg):
            assert isinstance(arg.type_, (FloatType, IntegerType))

            c_type, _ = type_to_cstr(arg.type_)
            return "{command_data_var}.{field_name} = static_cast<{c_type}>({field_json_var});\n".format(
                command_data_var=command_data_var_name,
                field_name=field_name,
                field_json_var=field_json_var_name,
                c_type=c_type
            )

        def generate_field_deserializer(command_data_var_name, command_json_var_name, arg):
            field_json_var_name = "field_output_json"
            field_name = arg.name

            field_present_test = '{command_json_var}.contains("{arg_field}")'.format(
                command_json_var=command_json_var_name,
                arg_field=field_name
            )

            picojson_type = self.__get_picojson_field_type(arg.type_)
            field_type_test = '{command_json_var}.get("{arg_field}").is<{picojson_type}>()'.format(
                command_json_var=command_json_var_name,
                arg_field=field_name,
                picojson_type=picojson_type
            )

            body = "{picojson_type} &{field_json_var} = " \
                   '{command_json_var}.get("{arg_field}").' \
                   "get<{picojson_type}>();\n".format(field_json_var=field_json_var_name,
                                                      picojson_type=picojson_type,
                                                      command_json_var=command_json_var_name,
                                                      arg_field=field_name)

            if isinstance(arg.type_, ArrayType):
                body += generate_array_field_deserializer(command_data_var_name, field_json_var_name, field_name, arg)
            elif isinstance(arg.type_, (FloatType, IntegerType)):
                body += generate_scalar_field_deserializer(command_data_var_name, field_json_var_name, field_name, arg)
            else:
                raise TypeError()

            tests = (
                field_present_test,
                field_type_test
            )

            return generate_tests_condition(tests, body)

        def generate_command_deserializer(profile_json_var_name, acc):
            command_data_var_name = "command_output"
            command_json_var_name = command_data_var_name + "_json"

            getter_cmd, setter_cmd = acc
            accessor_name = _get_accessor_name(getter_cmd)
            response_argstruct = self._argstructs[getter_cmd.response]
            getter_func_name = namespace_symbol(self.__protocol, getter_cmd.name)
            setter_func_name = namespace_symbol(self.__protocol, setter_cmd.name)
            arg_type_name = namespace_symbol(self.__protocol, response_argstruct.name)

            body = dedent("""\
            {type} command_output;
            if({getter}(handle, &{command_data_var}) != result_ok) {result_var} = result_error;
            picojson::value &{command_json_var} = {profile_data_var}.get(\"{cmd_field}\");
            """.format(
                type=arg_type_name,
                getter=getter_func_name,
                result_var=result_var_name,
                cmd_field=accessor_name,
                command_data_var=command_data_var_name,
                profile_data_var=profile_json_var_name,
                command_json_var=command_json_var_name
            ))
            for arg in response_argstruct.args:
                body += generate_field_deserializer(command_data_var_name, command_json_var_name, arg)
            body += "if({setter}(handle, &{command_data_var}) != result_ok) {result_var} = result_error;\n".format(
                setter=setter_func_name,
                command_data_var=command_data_var_name,
                result_var=result_var_name
            )

            has_command_test = '{profile_json_var}.contains("{accessor}")'.format(
                profile_json_var=profile_json_var_name,
                accessor=accessor_name
            )
            is_object_test = '{profile_json_var}.get("{accessor}").is<picojson::object>()'.format(
                profile_json_var=profile_json_var_name,
                accessor=accessor_name
            )

            tests = (
                has_command_test,
                is_object_test
            )

            return "if(" + " && ".join(tests) + ")" + "\n{\n" + indent(body, "    ") + "}\n"

        body = None

        profile_data_var_name = "profile_json"
        if not signature_only:
            body = dedent("""\
            result_t result = result_ok;
            picojson::value """ + profile_data_var_name + """;
            try
            {
                picojson::parse(""" + profile_data_var_name + """, buffer);
            }
            catch(const std::exception &)
            {
                return result_error;
            }
            if(!""" + profile_data_var_name + """.is<picojson::object>())
            {
                return result_error;
            }
            """)

            for acc in self._accessors:
                body += generate_command_deserializer(profile_data_var_name, acc)

            body += dedent("""
            return result;
            """)

        return self.__generate_function(
            "result_t", func_name, "device_t handle, char *buffer", body
        )

    def __generate_profiles_ascpect(self, for_header_inclusion):
        library_name = self.__get_library_name()

        if for_header_inclusion:
            return dedent("""\
            /**
             * \\~english
             * Load profile from device.
             * @param[in] handle - Device id.
             * @param[out] buffer - Pointer to output char* buffer. Memory for char* pointer must be allocated.
             * @param[out] allocate - Function for memory allocate.
             * \\~russian
             * Загружает профиль с устройства.
             * @param[in] handle - Идентификатор устройства.
             * @param[out] buffer -  Адрес указателя на выходной буфер.
             * Память для указателя на char* должна быть выделена.
             * @param[out] allocate - Функция для выделения памяти.
             */
            """ + self.__generate_get_profile_func(signature_only=True)) + "\n" + dedent("""\
            /**
             * \\~english
             * Save profile to device
             * @param[in] handle - Device id.
             * @param[in] buffer - Input char* buffer.
             * \\~russian
             * Загружает профиль с устройства.
             * @param[in] handle - Идентификатор устройства.
             * @param[in] buffer - Входной буфер, откуда будет считан профиль.
             */
            """ + self.__generate_set_profile_func(signature_only=True))
        else:
            result = '#include "{}.h"'.format(library_name) + dedent("""
            #include <algorithm>
            #include <stdexcept>
            #define PICOJSON_USE_INT64
            #define PICOJSON_USE_UINT64
            #include <picojson.h>
            """)
            result += self.__generate_get_profile_func(signature_only=False)
            result += self.__generate_set_profile_func(signature_only=False)
            return result

    def generate_profiles_impl_file(self):
        return self.__generate_profiles_ascpect(for_header_inclusion=False)

    def __generate_commands_aspect(self, for_header_inclusion):
        library_name = self.__get_library_name()

        bits = ['8', '16', '32', '64']
        primitive_types = []
        for b in bits:
            primitive_types.append("uint{}_t".format(b))
            primitive_types.append("int{}_t".format(b))
        primitive_types.append("float")
   
        generated_push = set()
        generated_pop = set()
        result = ""
        if for_header_inclusion:
            for index, flagset in enumerate(self.flagsets):
                if index > 0:
                    result += "\n"
                result += self.__generate_flagset(flagset)

            for index, argstruct in enumerate(self.argstructs):
                if index > 0:
                    result += "\n"
                result += self.__generate_argstruct(argstruct)
        else:
            result += '#include "{}.h"'.format(library_name) + dedent("""
            #include <map>
            #include <mutex>
            #include <cstring>
            #include <zf_log.h>
            #include "urpc.h"
            ZF_LOG_DEFINE_GLOBAL_OUTPUT_LEVEL;
            static std::map<device_t, urpc_device_handle_t> impl_by_handle;
            static std::mutex impl_by_handle_mutex;
            static void push_data(uint8_t **where, const void *data, size_t size)
            {
                memcpy(*where, data, size);
                *where += size;
            }
            
            #define GENERATE_PUSH(Type) \\
            static void push_##Type(uint8_t **where, Type value) { \\
                push_data(where, &value, sizeof(value)); \\
            }
            #define GENERATE_POP(Type) \\
            static Type pop_##Type(uint8_t **where) { \\
                Type result; \\
                memcpy(&result, *where, sizeof(result)); \\
                *where += sizeof(result); \\
                return (Type)result; \\
            }\n""")

        functions = ""
        functions += self.__generate_open_func(signature_only=for_header_inclusion) + "\n"
        functions += self.__generate_lib_version_func(signature_only=for_header_inclusion) + "\n"
        for f in self.__functions:
            functions += self.__generate_command_func(f, signature_only=for_header_inclusion) + "\n"
        functions += self.__generate_close_func(signature_only=for_header_inclusion) + "\n"
        for typename in primitive_types:
            pushname =  "push_{}".format(typename)
            popname = "pop_{}".format(typename)
            if pushname in functions and typename not in generated_push:
                generated_push.add(typename)
                result += dedent("""
                GENERATE_PUSH({t})
                """).format(t=typename)
            if popname in functions and typename not in generated_pop:
                generated_pop.add(typename)
                result += dedent("""
                GENERATE_POP({t})
                """).format(t=typename)
 
        result += functions
        return result

    def __get_library_name(self):
        return self.__protocol.name.lower()

    def __get_library_version(self):
        return self.__protocol

    def __get_build_indicator_macro_name(self):
        return "{}_URPC_BUILDING_STAGE".format(self.__protocol.name.upper())

    def __get_export_macro_name(self):
        return "{}_URPC_API_EXPORT".format(self.__protocol.name.upper())

    def __get_calling_convention_macro_name(self):
        return "{}_URPC_CALLING_CONVENTION".format(self.__protocol.name.upper())

    def generate_commands_impl_file(self):
        return self.__generate_commands_aspect(for_header_inclusion=False)

    def generate_example_file(self):
        project_name = self.name

        open_func = namespace_symbol(self.__protocol, "open_device")
        close_func = namespace_symbol(self.__protocol, "close_device")

        result = dedent(f"""\
        #include <iostream>
        #include "{project_name}.h"

        int main()
        {{
            // Enter path here, for example: com:///dev/ttyACM0, com:\\\\.\\COM1
            device_t device = {open_func}("<PATH_HERE>");
            if (device == device_undefined)
            {{
                std::cout << "Unable to open device" << std::endl;
                return 1;
            }}
            else
            {{
                std::cout << "Open OK" << std::endl;
            }}

            // Some commands here...

            {close_func}(&device);
            std::cout << "Close device" << std::endl;
            return 0;
        }}
        """)
        return result

    def generate_header_file(self):
        library_name = self.__get_library_name()
        include_guard_name = "INC_{}_H".format(library_name.upper())
        export_macro_name = self.__get_export_macro_name()
        build_indicator_macro_name = self.__get_build_indicator_macro_name()
        calling_convention_macro_name = self.__get_calling_convention_macro_name()

        result = dedent("""\
        /**
         * @file {project_name}.h
         * @brief {project_name} API
         */
        /* Project generated by builder {BUILDER_VERSION} */
        #ifndef {guard_name}
        #define {guard_name}
        #define {PROJECT_NAME}_BUILDER_VERSION_MAJOR {BUILDER_VERSION_MAJOR}
        #define {PROJECT_NAME}_BUILDER_VERSION_MINOR {BUILDER_VERSION_MINOR}
        #define {PROJECT_NAME}_BUILDER_VERSION_BUGFIX {BUILDER_VERSION_BUGFIX}
        #define {PROJECT_NAME}_BUILDER_VERSION_SUFFIX "{BUILDER_VERSION_SUFFIX}"
        #define {PROJECT_NAME}_BUILDER_VERSION "{BUILDER_VERSION}"

        """.format(
            project_name=self.name,
            PROJECT_NAME=self.name.upper(),
            BUILDER_VERSION_MAJOR=BUILDER_VERSION_MAJOR,
            BUILDER_VERSION_MINOR=BUILDER_VERSION_MINOR,
            BUILDER_VERSION_BUGFIX=BUILDER_VERSION_BUGFIX,
            BUILDER_VERSION_SUFFIX=BUILDER_VERSION_SUFFIX,
            BUILDER_VERSION=BUILDER_VERSION,
            guard_name=include_guard_name
        )) + dedent("""
        #ifdef __cplusplus
        extern "C"
        {
        #endif
        #include <stdint.h>
        #include <wchar.h>

        """) + dedent("""
        #undef {export_macro}
        #if defined(_WIN32)
            #if {build_indicator_macro}
                #define {export_macro} __declspec(dllexport)
            #else
                #define {export_macro} __declspec(dllimport)
            #endif
        #else
            #define {export_macro} __attribute__((visibility("default")))
        #endif
        """.format(
            export_macro=export_macro_name,
            build_indicator_macro=build_indicator_macro_name
        )) + dedent("""
        #undef {calling_convention_macro_name}
        #if defined(_WIN32)
            #define {calling_convention_macro_name} __cdecl
        #else
            #define {calling_convention_macro_name}
        #endif
        """).format(
            calling_convention_macro_name=calling_convention_macro_name
        ) + dedent("""
        typedef int device_t;
        #define device_undefined (-1)
        typedef int result_t;
        #define result_ok 0
        #define result_error (-1)
        #define result_not_implemented (-2)
        #define result_value_error (-3)
        #define result_nodevice (-4)
        #define result_timeout (-5)

        #define STR_result_ok_0 "result_ok 0"
        #define STR_device_undefined_1 "device_undefined (-1)"
        #define STR_result_error_1 "result_error (-1)"
        #define STR_result_not_implemented_2 "result_not_implemented (-2)"
        #define STR_result_value_error_3 "result_value_error (-3)"
        #define STR_result_nodevice_4 "result_nodevice (-4)"
        #define STR_result_timeout_5 "result_timeout (-5)"

        """) + self.__generate_logging_aspect(
            for_header_inclusion=True
        ) + self.__generate_commands_aspect(
            for_header_inclusion=True
        ) + self.__generate_profiles_ascpect(
            for_header_inclusion=True
        ) + dedent("""
        #ifdef __cplusplus
        }
        #endif
        #endif
        """)

        return result

    def generate_gcc_export_symbols_file(self):
        library_name = self.__get_library_name()

        return dedent("""\
        {{
            global: {library_name}_*;
            local: *;
        }};
        """).format(
            library_name=library_name
        )

    def generate_rc_file(self):

        major, minor, release = 0, 0, 0
        if self.__protocol.version.count(".") == 2:
            major, minor, release = self.__protocol.version.split(".")

        if self.__protocol.version.count(".") == 1:
            major, minor = self.__protocol.version.split(".")

        if self.__protocol.version.isdigit():
            major = self.__protocol.version

        libname = self.__protocol.name.lower()
        text = dedent(f"""\
        #include <windows.h>

        #define VOS_NT_WINDOWS32    0x00040004L
        #define VFT_APP             0x00000001L

        1 VERSIONINFO
        FILEVERSION {major},{minor},{release},100
        PRODUCTVERSION {BUILDER_VERSION_MAJOR},{BUILDER_VERSION_MINOR},{BUILDER_VERSION_BUGFIX},100
        FILEOS VOS_DOS_WINDOWS32
        FILETYPE VFT_APP
        {{
            BLOCK "StringFileInfo"
            {{
                BLOCK "040904E4"
                {{
                    VALUE "CompanyName", "COMPANY NAME HERE\\0"
                    VALUE "FileDescription", "{libname} library\\0"
                    VALUE "FileVersion", "{self.__protocol.version}\\0"
                    VALUE "InternalName", "{libname}\\0"
                    VALUE "LegalCopyright", "MIT License\\0"
                    VALUE "OriginalFilename", "{libname}.dll\\0"
                    VALUE "ProductName", "{libname}\\0"
                    VALUE "ProductVersion","{BUILDER_VERSION_MAJOR}.{BUILDER_VERSION_MINOR}.{BUILDER_VERSION_BUGFIX}\\0"
                }}
            }}
            BLOCK "VarFileInfo"
            {{
                VALUE "Translation", 1033, 1252
            }}
        }}
        """)

        return text

    def generate_cmake_file(self, files):
        library_name = self.__get_library_name()
        library_target_name = library_name
        library_name_uppercase = library_name.upper()
        build_indicator_macro_name = self.__get_build_indicator_macro_name()

        return dedent("""\
        # Project generated by builder {BUILDER_VERSION}
        CMAKE_MINIMUM_REQUIRED(VERSION 3.2)
        SET(CMAKE_CXX_STANDARD 11)
        PROJECT({library_target} CXX)

        # Hide symbols automatically, if this is GNU-compatible compiler
        IF(
            ("${{CMAKE_CXX_COMPILER_ID}}" STREQUAL GNU)
            OR ("${{CMAKE_CXX_COMPILER_ID}}" STREQUAL Clang)
            OR ("${{CMAKE_CXX_COMPILER_ID}}" STREQUAL AppleClang)
        )
            set({library_name_uppercase}_AUTO_HIDE_SYMBOLS YES)
        ELSE()
            set({library_name_uppercase}_AUTO_HIDE_SYMBOLS NO)
        ENDIF()
        OPTION(
            {library_name_uppercase}_HIDE_SYMBOLS
            "Hide non-API symbols of library"
            ${{{library_name_uppercase}_AUTO_HIDE_SYMBOLS}}
        )
        OPTION(
            {library_name_uppercase}_STATIC_STD_LIBS
            "Link libgcc and libstdc++ statically, if available"
            NO
        )
        OPTION(
            {library_name_uppercase}_BUILD_EXAMPLE
            "Build console example"
            OFF
        )
        IF(${{{library_name_uppercase}_HIDE_SYMBOLS}})
            set(
                CMAKE_SHARED_LINKER_FLAGS
                ${{CMAKE_SHARED_LINKER_FLAGS}}
                "-Wl,--version-script=${{CMAKE_CURRENT_SOURCE_DIR}}/gcc_export_symbols"
            )
        ELSE()
            MESSAGE(
                NOTICE: " Won't hide non-API library symbols. Оn some platforms it may cause segmentation faults."
            )
        ENDIF()
        IF(${{CMAKE_SYSTEM_NAME}} STREQUAL Darwin)
            # It is required to build a rpath framework
            CMAKE_POLICY(SET CMP0042 NEW)
        ENDIF()
        IF(${{CMAKE_SYSTEM_NAME}} STREQUAL Darwin)
            # It is required to build a rpath framework
            CMAKE_POLICY(SET CMP0042 NEW)
        ENDIF()
        if(${{CMAKE_SYSTEM_NAME}} STREQUAL Windows)
            add_definitions( -D_CRT_SECURE_NO_WARNINGS)
        endif()
        ADD_LIBRARY({library_target} SHARED {library_target_files} version.rc)
        SET_TARGET_PROPERTIES({library_target} PROPERTIES C_VISIBILITY_PRESET hidden)
        SET_TARGET_PROPERTIES({library_target} PROPERTIES CXX_VISIBILITY_PRESET hidden)
        SET_TARGET_PROPERTIES({library_target} PROPERTIES VISIBILITY_INLINES_HIDDEN TRUE)
        SET_TARGET_PROPERTIES({library_target} PROPERTIES COMPILE_DEFINITIONS "{build_indicator_macro}")
        SET_TARGET_PROPERTIES({library_target} PROPERTIES PUBLIC_HEADER {library_name_lowercase}.h)

        IF(UNIX)
            include(GNUInstallDirs)
            INSTALL(TARGETS {library_target}
                LIBRARY DESTINATION ${{CMAKE_INSTALL_LIBDIR}}
                PUBLIC_HEADER DESTINATION ${{CMAKE_INSTALL_INCLUDEDIR}})
        ENDIF()

        if(MSVC)
<<<<<<< HEAD
            target_compile_options({library_target} PRIVATE /W3 /WX)
        else()
            target_compile_options({library_target} PRIVATE -Wall -Wextra -Werror)
=======
           target_compile_options({library_target} PRIVATE /W3 /WX)
        endif()

        if(UNIX)
           target_compile_options({library_target} PRIVATE -Wall -Wextra -Werror)
>>>>>>> 0e6cd8d69a85641b89d5ec22b5c278939a0d43d1
        endif()

        FUNCTION(ADD_LIBRARY_URPC)
            SET(CMAKE_POSITION_INDEPENDENT_CODE ON)
            SET(BUILD_SHARED_LIBS OFF CACHE INTERNAL "")
            SET(URPC_ENABLE_XINET ON CACHE INTERNAL "")
            SET(URPC_ENABLE_SERIAL ON CACHE INTERNAL "")
            SET(URPC_ENABLE_UDP ON CACHE INTERNAL "")
            SET(ZF_LOG_LIBRARY_PREFIX "{library_target}_" CACHE INTERNAL "")
            SET(ZF_LOG_OPTIMIZE_SIZE OFF CACHE INTERNAL "")
            SET(ZF_LOG_USE_ANDROID_LOG OFF CACHE INTERNAL "")
            SET(ZF_LOG_USE_DEBUGSTRING OFF CACHE INTERNAL "")
            SET(ZF_LOG_USE_NSLOG OFF CACHE INTERNAL "")
            ADD_SUBDIRECTORY(vendor/liburpc)
        ENDFUNCTION()
        ADD_LIBRARY_URPC()
        SET_TARGET_PROPERTIES(zf_log PROPERTIES COMPILE_DEFINITIONS ZF_LOG_EXTERN_GLOBAL_OUTPUT)
        TARGET_INCLUDE_DIRECTORIES({library_target} PRIVATE vendor vendor/liburpc vendor/liburpc/vendor/zf_log/zf_log)
        IF(${{CMAKE_SYSTEM_NAME}} STREQUAL Windows)
            set({library_name_uppercase}_LINK_LIBRARIES urpc  Ws2_32)
        ELSE ()
            set({library_name_uppercase}_LINK_LIBRARIES urpc)
        ENDIF()
        IF(
            (${{{library_name_uppercase}_STATIC_STD_LIBS}})
            AND (
                ("${{CMAKE_CXX_COMPILER_ID}}" STREQUAL GNU)
                OR ("${{CMAKE_CXX_COMPILER_ID}}" STREQUAL Clang)
                OR ("${{CMAKE_CXX_COMPILER_ID}}" STREQUAL AppleClang)
            )
        )
            SET(
                {library_name_uppercase}_LINK_LIBRARIES
                "${{{library_name_uppercase}_LINK_LIBRARIES}}" -static-libgcc -static-libstdc++
            )
        ENDIF()
        TARGET_LINK_LIBRARIES({library_target} ${{{library_name_uppercase}_LINK_LIBRARIES}})

        SET({library_name_uppercase}_INCLUDE_DIRS ${{CMAKE_INSTALL_INCLUDEDIR}})
        SET({library_name_uppercase}_LIBRARIES
            ${{CMAKE_INSTALL_LIBDIR}}/${{CMAKE_SHARED_LIBRARY_PREFIX}}{library_target}${{CMAKE_SHARED_LIBRARY_SUFFIX}})
        INCLUDE(CMakePackageConfigHelpers)
        CONFIGURE_PACKAGE_CONFIG_FILE(
            "${{PROJECT_SOURCE_DIR}}/cmake/{library_target}Config.cmake.in"
            "${{PROJECT_BINARY_DIR}}/{library_target}Config.cmake"
            INSTALL_DESTINATION ${{CMAKE_INSTALL_DATAROOTDIR}}/{library_target}/cmake
            PATH_VARS {library_name_uppercase}_INCLUDE_DIRS {library_name_uppercase}_LIBRARIES
            NO_CHECK_REQUIRED_COMPONENTS_MACRO
        )
        INSTALL(FILES "${{PROJECT_BINARY_DIR}}/{library_target}Config.cmake"
                DESTINATION ${{CMAKE_INSTALL_DATAROOTDIR}}/{library_target}/cmake)

        IF({library_name_uppercase}_BUILD_EXAMPLE)
            ADD_EXECUTABLE({library_name_uppercase}_example example.cpp)
            TARGET_LINK_LIBRARIES({library_name_uppercase}_example {library_target})
            IF(WIN32)
                SET_PROPERTY(DIRECTORY ${{CMAKE_CURRENT_SOURCE_DIR}}
                             PROPERTY VS_STARTUP_PROJECT {library_name_uppercase}_example)
            ENDIF()
        ENDIF()
        """).format(
            BUILDER_VERSION=BUILDER_VERSION,
            library_target=library_target_name,
            library_name_uppercase=library_name_uppercase,
            build_indicator_macro=build_indicator_macro_name,
            library_target_files=" ".join(files),
            library_name_lowercase=library_name
        )

    def generate_cmake_include(self):
        return dedent("""\
        @PACKAGE_INIT@

        set_and_check({library_name_uppercase}_INCLUDE_DIRS "@PACKAGE_{library_name_uppercase}_INCLUDE_DIRS@")
        set_and_check({library_name_uppercase}_LIBRARIES "@PACKAGE_{library_name_uppercase}_LIBRARIES@")
        """.format(
            library_name_uppercase=self.__get_library_name().upper()
        ))


def build(protocol, output):
    view = _ClibBuilderImpl(protocol)

    gen_by_file_name = {
        "{}.h".format(view.name): view.generate_header_file,
        "commands.cpp": view.generate_commands_impl_file,
        "logging.cpp": view.generate_logging_impl_file,
        "profiles.cpp": view.generate_profiles_impl_file,
    }

    resources_path = join_path(abspath(dirname(__file__)), "resources")
    path_prefix_in_archive = view.name
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for file_name, gen in gen_by_file_name.items():
            archive.writestr(join_path(path_prefix_in_archive, file_name), gen())
        archive.writestr(
            join_path(path_prefix_in_archive, "gcc_export_symbols"),
            view.generate_gcc_export_symbols_file()
        )
        archive.writestr(
            join_path(path_prefix_in_archive, "CMakeLists.txt"),
            view.generate_cmake_file(gen_by_file_name.keys())
        )
        archive.writestr(
            join_path(path_prefix_in_archive, "version.rc"),
            view.generate_rc_file()
        )
        archive.writestr(
            join_path(path_prefix_in_archive, "example.cpp"),
            view.generate_example_file()
        )
        archive.writestr(
            join_path(path_prefix_in_archive, "cmake", "{}Config.cmake.in".format(view.name)),
            view.generate_cmake_include()
        )
        for real_path in resources(resources_path):
            commonprefix_len = len(commonprefix((resources_path, real_path)))
            archive.write(
                real_path,
                join_path(path_prefix_in_archive, real_path[commonprefix_len + 1:])
            )
