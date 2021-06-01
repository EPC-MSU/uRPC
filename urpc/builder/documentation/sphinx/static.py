from textwrap import dedent


def get_static_part(protocol):
    s = dedent("""
                Communication protocol specification
                ====================================

                Communication protocol v{0}

                .. contents::
                  :local:

                Protocol description
                --------------------

                Controller can be controlled from the PC using serial connection
                (COM-port). COM-port parameters are fixed controller-side:

                - Speed: 115200 baud
                - Frame size: 8 bits
                - Stop-bits: 2 bits
                - Parity: none
                - Flow control: none
                - Byte receive timeout: 400 ms
                - Bit order: little endian
                - Byte order: little endian

                Command execution
                -----------------

                All data transfers are initiated by the PC, meaning that the
                controller waits for incoming commands and replies accordingly. Each
                command is followed by the controller response, with rare exceptions
                of some service commands. One should not send another command without
                waiting for the previous command answer.

                Commands are split into service, general control and general
                information types.
                Commands are executed immediately. Parameters which are set by Sxxx
                commands are applied no later than 1ms after acknowledgement.
                Command processing does not affect real-time engine control (PWM,
                encoder readout, etc).

                Both controller and PC have an IO buffer. Received commands and
                command data are processed once and then removed from buffer.
                Each command consists of 4-byte identifier and optionally a data
                section followed by its 2-byte CRC. Data can be transmitted in both
                directions, from PC to the controller and vice versa. Command is
                scheduled for execution if it is a legitimate command and (in case of
                data) if its CRC matches. After processing a correct command
                controller replies with 4 bytes - the name of processed command,
                followed by data and its 2-byte CRC, if the command is supposed to
                return data.

                Controller-side error processing
                --------------------------------

                Wrong command or data
                ~~~~~~~~~~~~~~~~~~~~~

                If the controller receives a command that cannot be interpreted as a
                legitimate command, then controller ignores this command, replies with
                an "errc" string and sets "command error" flag in the current status
                data structure. If the unreconized command contained additional data,
                then it can be interpreted as new command(s). In this case
                resynchronization is required.

                If the controller receives a valid command with data and its CRC
                doesn't match the CRC computed by the controller, then controller
                ignores this command, replies with an "errd" string and sets "data
                error" flag in the current status data structure. In this case
                synchronization is not needed.

                CRC calculation
                ~~~~~~~~~~~~~~~

                CRC is calculated for data only, 4-byte command identifier is not
                included. CRC algorithm in C is as follows:

                .. code-block:: c

                    unsigned short CRC16(INT8U *pbuf, unsigned short n)
                    {{
                      unsigned short crc, i, j, carry_flag, a;
                      crc = 0xffff;
                      for(i = 0; i < n; i++)
                      {{
                        crc = crc ^ pbuf[i];
                        for(j = 0; j < 8; j++)
                        {{
                          a = crc;
                          carry_flag = a & 0x0001;
                          crc = crc >> 1;
                          if ( carry_flag == 1 ) crc = crc ^ 0xa001;
                        }}
                      }}
                      return crc;
                    }}


                This function receives a pointer to the data array, pbuf, and data
                length in bytes, n. It returns a two byte CRC code.

                **The example of CRC calculation:**

                **Command code (CMD):** \"home\" or 0x656D6F68

                .. code-block:: c

                  0x68 0x6F 0x6D 0x65
                  CMD

                **Command code (CMD):** \"gpos\" or 0x736F7067

                .. code-block:: c

                   0x67 0x70 0x6F 0x73
                   CMD

                **Command code (CMD):** \"movr\" or 0x72766F6D

                .. code-block:: c

                   0x6D 0x6F 0x76 0x72  0x00 0x00 0x00 0xC8  0x00 0x00  0x00 0x00 0x00 0x00 0x00 0x00  0x53 0xc7
                   CMD                  DeltaPosition        uDPos      Reserved                       CRC

                .. figure:: crc.png
                  :align: center

                Transmission errors
                ~~~~~~~~~~~~~~~~~~~

                Most probable transmission errors are missing, extra or altered byte.
                In usual settings transmission errors happen rarely, if at all.

                Frequent errors are possible when using low-quality or broken
                USB-cable or board interconnection cable. Protocol is not designed for
                use in noisy environments and in rare cases an error may match a valid
                command code and get executed.

                Missing byte, controller side
                """""""""""""""""""""""""""""""

                A missing byte on the controller side leads to a timeout on the PC
                side. Command is considered to be sent unsuccessfully by the PC.
                Synchronization is momentarily disrupted and restored after a timeout.

                Missing byte, PC side
                """"""""""""""""""""""""

                A missing byte on the PC side leads to a timeout on PC side.
                Synchronization is maintained.

                Extra byte, controller side
                """"""""""""""""""""""""""""""

                An extra byte received by the controller leads to one or several
                "errc" or "errd" responses. Command is considered to be sent
                unsuccessfully by the PC. Receive buffer may also contain one or
                several "errc" or "errd" responses. Synchronization is disrupted.

                Extra byte, PC side
                """"""""""""""""""""""""

                An extra byte received by the PC leads to an incorrectly interpreted
                command or CRC and an extra byte in the receive buffer.
                Synchronization is disrupted.

                Altered byte, controller side
                """"""""""""""""""""""""""""""

                An altered byte received by the controller leads to one or several
                "errc" or "errd" responses. Command is considered to be sent
                unsuccessfully by the PC. Receive buffer may also contain one or
                several "errc" or "errd" responses. Synchronization can rarely be
                disrupted, but is generally maintained.

                Altered byte, PC side
                """"""""""""""""""""""""

                An altered byte received by the PC leads to an incorrectly interpreted
                command or CRC. Synchronization is maintained.

                Timeout resynchronization
                ~~~~~~~~~~~~~~~~~~~~~~~~~

                If during packet reception next byte wait time exceeds timeout value,
                then partially received command is ignored and receive buffer is
                cleared. Controller timeout should be less than PC timeout, taking into
                account time it takes to transmit the data.

                Zero byte resynchronization
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~

                There are no command codes that start with a zero byte ('\\\\0'). This
                allows for a following synchronization procedure: controller always
                answers with a zero byte if the first command byte is zero, PC ignores
                first response byte if it is a zero byte. Then, if synchronization is
                disrupted on either side the following algorithm is used:

                In case PC receives "errc", "errd" or a wrong command answer code,
                then PC sends 4 to 250 zeroes to the controller (250 byte limit is
                caused by input buffer length and usage of I2C protocol, less than 4
                zeroes do not guarantee successful resynchronization). During this
                time PC continuously reads incoming bytes from the controller until
                the first zero is received and stops sending and receiving right after
                that.

                Received zero byte is likely not a part of a response to a previous
                command because on error PC receives "errc"/"errd" response. It is
                possible in rare cases, then synchronization procedure will start
                again. Therefore first zero byte received by the PC means that
                controller input buffer is already empty and will remain so until any
                command is sent. Right after receiving first zero byte from the
                controller PC is ready to transmit next command code. The rest of zero
                bytes in transit will be ignored because they will be received before
                controller response.

                This completes the zero byte synchronization procedure.

                Library-side error processing
                -----------------------------

                Nearly every library function has a return status of type `result_t`.

                After sending command to the controller library reads incoming bytes
                until a non-zero byte is received. All zero bytes are ignored. Library
                reads first 4 bytes and compares them to the command code. It then
                waits for data section and CRC, if needed. If first 4 received bytes
                do not match the sent command identifier, then zero byte
                synchronization procedure is launched, command is considered to be
                sent unsuccessfully. If first 4 received bytes match the sent command
                identifier and command has data section, but the received CRC doesn't
                match CRC calculated from the received data, then zero byte
                synchronization procedure is launched, command is considered to be
                sent unsuccessfully. If a timeout is reached while the library is
                waiting for the controller response, then zero byte synchronization
                procedure is launched, command is considered to be sent
                unsuccessfully.

                If no errors were detected, then command is considered to be
                successfully completed and `result_ok` is returned.

                .. figure:: Synch.png
                  :align: center

                Library return codes
                ~~~~~~~~~~~~~~~~~~~~

                -  `result_ok`. No errors detected.
                -  `result_error`. Generic error. Can happen because of hardware
                   problems, empty port buffer, timeout or successfull synchronization
                   after an error. Another common reason for this error is protocol
                   version mismatch between controller firmware and PC library.
                -  `result_nodevice`. Error opening device, lost connection or failed
                   synchronization. Device reopen and/or user action is required.

                If a function returns an error values of all parameters it writes to are
                undefined. Error code may be accompanied by detailed error description
                output to system log (Unix-like OS) or standard error (Windows-like OS).

                Zero byte synchronization procedure
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

                Synchronization is performed by means of sending zero ('\\\\0') bytes and
                reading bytes until a zero byte is received. Optionally one may clear
                port buffer at the end of synchronization procedure. Initially 64 zero
                bytes are sent. If there were no zero bytes received during the timeout,
                then a string of 64 bytes is sent 3 more times. After 4 unsuccessful
                attempts and no zero bytes received device is considered lost. In this
                case library should return `result_nodevice` error code. In case of
                successful syncronization library returns `result_error`.

                Controller error response types
                -------------------------------

                ERRC
                ~~~~

                **Answer:** (4 bytes)

                **Code:** "errc" or 0x63727265

                .. csv-table::
                   :class: longtable
                   :widths: 2, 8, 6

                   "uint32_t", "errc", "Command error"

                **Description:**

                Controller answers with "errc" if the command is either not recognized
                or cannot be processed and sets the correspoding bit in status data
                structure.

                ERRD
                ~~~~

                **Answer:** (4 bytes)

                **Code:** "errd" or 0x64727265


                .. csv-table::
                   :class: longtable
                   :widths: 2, 8, 6

                   "uint32_t", "errd", "Data error"

                **Description:**

                Controller answers with "errd" if the CRC of the data section computed
                by the controller doesn't match the received CRC field and sets the
                correspoding bit in status data structure.

                ERRV
                ~~~~

                **Answer:** (4 bytes)

                **Code:** "errv" or 0x76727265

                .. csv-table::
                   :class: longtable
                   :widths: 2, 8, 6

                   "uint32_t", "errv", "Value error"

                **Description:**

                Controller answers with "errv" if any of the values in the command are
                out of acceptable range and can not be applied. Inacceptable value is
                replaced by a rounded, truncated or default value. Controller also
                sets the correspoding bit in status data structure.

                All controller commands
                -----------------------

            """.format(protocol.version))
    return s[1:]  # remove first line


def get_ru_static_part(protocol):
    s = dedent("""
                msgid ""
                msgstr ""
                "MIME-Version: 1.0\\n"
                "Content-Type: text/plain; charset=UTF-8\\n"
                "Content-Transfer-Encoding: 8bit\\n"
                "Language: ru\\n"

                msgid "Communication protocol specification"
                msgstr "Описание протокола обмена"

                msgid "Communication protocol v{0}"
                msgstr "Описание протокола v{0}"

                msgid "Protocol description"
                msgstr "Описание протокола"

                msgid ""
                "Controller can be controlled from the PC using serial connection (COM-port). COM-"
                "port parameters are fixed controller-side:"
                msgstr ""
                "Управление контроллером с ПК происходит по интерфейсу последовательного порта "
                "(COM-порт). На стороне контроллера жёстко установлены следующие параметры COM-"
                "порта:"

                msgid "Speed: 115200 baud"
                msgstr "Скорость – 115200 бод"

                msgid "Frame size: 8 bits"
                msgstr "Длина кадра – 8 бит"

                msgid "Stop-bits: 2 bits"
                msgstr "Стоп-биты – 2 бита"

                msgid "Parity: none"
                msgstr "Чётность – нет"

                msgid "Flow control: none"
                msgstr "Контроль потока – нет (Xon/Xoff, CTS/RTS не используются)"


                msgid "Byte receive timeout: 400 ms"
                msgstr "Таймаут на получение, между байтами одного пакета – 400 мсек"

                msgid "Bit order: little endian"
                msgstr "Порядок следования бит – LittleEndian"

                msgid "Byte order: little endian"
                msgstr "Многобайтовые типы данных передаются младшим байтом вперёд"

                msgid "Command execution"
                msgstr "Исполнение команд"

                msgid ""
                "All data transfers are initiated by the PC, meaning that the controller waits "
                "for incoming commands and replies accordingly. Each command is followed by the "
                "controller response, with rare exceptions of some service commands. One should "
                "not send another command without waiting for the previous command answer."
                msgstr ""
                "Базовый принцип протокола - \\"Запрос-Ответ\\", причём все обмены данными "
                "инициируются ПК, т.е. ПК посылает команды в контроллер, но не наоборот. Каждая "
                "команда подразумевает получение ответа от контроллера (кроме редких случаев "
                "специальных команд), т.е. нельзя послать несколько команд подряд, без ожидания "
                "ответа на них."

                msgid ""
                "Commands are split into service, general control and general information types. "
                "Commands are executed immediately. Parameters which are set by Sxxx commands are "
                "applied no later than 1ms after acknowledgement. Command processing does not "
                "affect real-time engine control (PWM, encoder readout, etc)."
                msgstr ""
                "Все команды делятся на сервисные, штатные управляющие и штатные информационные. "
                "Команды выполняются сразу после их поступления в контроллер. Установленные "
                "командой SХХХ параметры начинают влиять на текущее движение в течение 1 мс после "
                "установки. Обработка команды не влияет на своевременность выполнения "
                "контроллером действий связанных с оперативным управление и контролем двигателя "
                "(работа ШИМ, взаимодействие с энкодером и т.п.)."

                msgid ""
                "Both controller and PC have an IO buffer. Received commands and command data are "
                "processed once and then removed from buffer. Each command consists of 4-byte "
                "identifier and optionally a data section followed by its 2-byte CRC. Data can be "
                "transmitted in both directions, from PC to the controller and vice versa. "
                "Command is scheduled for execution if it is a legitimate command and (in case of "
                "data) if its CRC matches. After processing a correct command controller replies "
                "with 4 bytes - the name of processed command, followed by data and its 2-byte "
                "CRC, if the command is supposed to return data."
                msgstr ""
                "И контроллер и ПК обладают буфером обмена. Принятые команды и данные, в случае "
                "их наличия в команде, обрабатываются один раз. То есть, после обработки эти "
                "данные удаляются из буфера и обрабатываются уже новые пришедшие байты. Каждая "
                "команда состоит из четырёхбайтной строки, данных (если команда их "
                "предусматривает) и двухбайтного кода контроля CRC если команда содержит данные. "
                "Данные могут пересылаться как из компьютера, так и контроллером. Команда "
                "передаётся на обработку если она распознана и, в случае передачи данных, код CRC "
                "верный. После обработки пришедшей без ошибок команды контроллер посылает в "
                "компьютер четырехбайтную строку – наименование выполненной команды, затем "
                "данные, если формат команды это предусматривает, затем два байта CRC (если есть "
                "данные)."

                msgid "Controller-side error processing"
                msgstr "Обработка ошибок на стороне контроллера"

                msgid "Wrong command or data"
                msgstr "Неверные команды или данные"

                msgid ""
                "If the controller receives a command that cannot be interpreted as a legitimate "
                "command, then controller ignores this command, replies with an \\"errc\\" string "
                "and sets \\"command error\\" flag in the current status data structure. If the "
                "unreconized command contained additional data, then it can be interpreted as new "
                "command(s). In this case resynchronization is required."
                msgstr ""
                "Если пришедшая в контроллер команда не может быть интерпретирована, как "
                "определенная команда управления, то в компьютер посылается строка \\"errc\\", "
                "команда игнорируется, в данных текущего состояния контроллера выставляется бит "
                "\\"команда не распознана\\". Если неопознанная команда содержала данные, то "
                "возможно неверная интерпретация принятых данных как новых команд. Необходима "
                "синхронизация."

                msgid ""
                "If the controller receives a valid command with data and its CRC doesn't match "
                "the CRC computed by the controller, then controller ignores this command, "
                "replies with an \\"errd\\" string and sets \\"data error\\" flag in the current "
                "status data structure. In this case synchronization is not needed."
                msgstr ""
                "Если пришедшая в контроллер команда интерпретирована верно, команда "
                "предусматривала данные, они пришли, но два байта CRC не соответствует полученным "
                "с ней данным, то в данных текущего состояния контроллера устанавливается флаг "
                "ошибки CRC пришедших данных, в компьютер посылается строка \\"errd\\", текущая "
                "команда игнорируется. Синхронизация приёма/передачи с компьютером не нужна."

                msgid "CRC calculation"
                msgstr "Расчёт CRC"

                msgid ""
                "CRC is calculated for data only, 4-byte command identifier is not included. CRC "
                "algorithm in C is as follows:"
                msgstr ""
                "CRC рассчитывается для передаваемых данных. Четыре байта команды в расчёте не "
                "участвуют. Алгоритм CRC на языке Си:"

                msgid ""
                "This function receives a pointer to the data array, pbuf, and data length in "
                "bytes, n. It returns a two byte CRC code."
                msgstr ""
                "Функция получает указатель на массив данных pbuf, длину данных в байтах n. "
                "Функция возвращает двубайтное слово - код CRC."

                msgid "**The example of CRC calculation:**"
                msgstr "**Пример расчёта CRC:**"

                msgid "**Command code (CMD):** \\"home\\" or 0x656D6F68"
                msgstr "**Код команды (CMD):** \\"home\\" или 0x656D6F68"

                msgid "**Command code (CMD):** \\"gpos\\" or 0x736F7067"
                msgstr "**Код команды (CMD):** \\"gpos\\" или 0x736F7067"

                msgid "**Command code (CMD):** \\"movr\\" or 0x72766F6D"
                msgstr "**Код команды (CMD):** \\"movr\\" или 0x72766F6D"

                msgid "Transmission errors"
                msgstr "Сбои передачи"

                msgid ""
                "Most probable transmission errors are missing, extra or altered byte. In usual "
                "settings transmission errors happen rarely, if at all."
                msgstr ""
                "Наиболее вероятны следующие сбои в канале связи: исчезновение байта при приёме "
                "или передаче контроллером, возникновение лишнего байта при приёме или передаче "
                "контроллером и изменение принятого или посланного байта.Сбои происходят при "
                "нестандартных условиях и обычно не наблюдаются вообще."

                msgid ""
                "Frequent errors are possible when using low-quality or broken USB-cable or board "
                "interconnection cable. Protocol is not designed for use in noisy environments "
                "and in rare cases an error may match a valid command code and get executed."
                msgstr ""
                "Регулярные сбои возможны при некачественном, сломанном кабеле USB или "
                "соединительном кабеле между платами. Протокол не разрабатывался для штатного "
                "применения в условиях сильно нестабильной связи. В частности в таких условиях "
                "редко возможно выполнение не той команды, что была послана."

                msgid "Missing byte, controller side \\""
                msgstr "Исчезновение байта на стороне контроллера"

                msgid ""
                "A missing byte on the controller side leads to a timeout on the PC side. Command "
                "is considered to be sent unsuccessfully by the PC. Synchronization is "
                "momentarily disrupted and restored after a timeout."
                msgstr ""
                "Байт, ожидаемый, но не полученный контроллером, приводит к таймауту компьютера. "
                "Посылка команды считается компьютером неуспешной. На этот момент синхронизация "
                "передачи данных будет нарушена, но восстановится по таймауту (если таймаут "
                "контроллера меньше таймаута компьютера с учётом времени пересылки)."

                msgid "Missing byte, PC side"
                msgstr "Исчезновение байта на стороне компьютера"

                msgid ""
                "A missing byte on the PC side leads to a timeout on PC side. Synchronization is "
                "maintained."
                msgstr ""
                "Байт, не полученный компьютером, приводит к таймауту компьютера. Синхронизация "
                "не нарушена."

                msgid "Extra byte, controller side"
                msgstr "Возникновение байта на стороне контроллера"

                msgid ""
                "An extra byte received by the controller leads to one or several \\"errc\\" or "
                "\\"errd\\" responses. Command is considered to be sent unsuccessfully by the PC. "
                "Receive buffer may also contain one or several \\"errc\\" or \\"errd\\" responses. "
                "Synchronization is disrupted."
                msgstr ""
                "Лишний байт, возникший при приёме контроллером, приводит к получению компьютером "
                "одного или нескольких \\"errc\\" либо \\"errd\\" (очень редко сочетания \\"errc\\" и "
                "\\"errd\\"). Посылка команды считается неуспешной. В приёмном буфере компьютера "
                "может появиться несколько \\"errc\\" или \\"errd\\" ответов контроллера. На этот "
                "момент синхронизация нарушена."

                msgid "Extra byte, PC side"
                msgstr "Возникновение байта на стороне компьютера"

                msgid ""
                "An extra byte received by the PC leads to an incorrectly interpreted command or "
                "CRC and an extra byte in the receive buffer. Synchronization is disrupted."
                msgstr ""
                "Байт, возникший при приёме компьютером, приводит к неверно принятой команде или "
                "неверному коду CRC. Кроме того, в приёмном буфере останется лишний байт. На этот "
                "момент синхронизация нарушена."

                msgid "Altered byte, controller side"
                msgstr "Изменение байта на стороне контроллера"

                msgid ""
                "An altered byte received by the controller leads to one or several \\"errc\\" or "
                "\\"errd\\" responses. Command is considered to be sent unsuccessfully by the PC. "
                "Receive buffer may also contain one or several \\"errc\\" or \\"errd\\" responses. "
                "Synchronization can rarely be disrupted, but is generally maintained."
                msgstr ""
                "Байт, изменившийся при приёме контроллером, приводит к получению компьютером "
                "одного или нескольких \\"errc\\" либо \\"errd\\" (очень редко сочетания \\"errc\\" и "
                "\\"errd\\"). Посылка команды считается неуспешной. В приёмном буфере компьютера "
                "может появиться несколько \\"errc\\" либо \\"errd\\" ответов контроллера. Обычно "
                "синхронизация не нарушается, но редко она может быть нарушена."

                msgid "Altered byte, PC side"
                msgstr "Изменение байта на стороне компьютера"

                msgid ""
                "An altered byte received by the PC leads to an incorrectly interpreted command "
                "or CRC. Synchronization is maintained."
                msgstr ""
                "Байт, изменившийся при приёме компьютером, приводит к неверно принятой команде "
                "или неверному коду CRC. На этот момент синхронизация не нарушена."

                msgid "Timeout resynchronization"
                msgstr "Восстановление синхронизации методом таймаута"

                msgid ""
                "If during packet reception next byte wait time exceeds timeout value, then "
                "partially received command is ignored and receive buffer is cleared. Controller "
                "timeout should be less than PC timeout, taking into account time it takes to "
                "transmit the data."
                msgstr ""
                "Если при получении пакета, время между получением одного или нескольких байт "
                "выходит за рамки таймаута, то полученные данные игнорируются, входной буфер "
                "очищается. Время таймаута контроллера должно быть меньше таймаута компьютера с "
                "учетом погрешности на время пересылки."

                msgid "Zero byte resynchronization"
                msgstr "Восстановление синхронизации методом очистительных нулей"

                msgid ""
                "There are no command codes that start with a zero byte ('\\\\\\\\0'). This allows for "
                "a following synchronization procedure: controller always answers with a zero "
                "byte if the first command byte is zero, PC ignores first response byte if it is "
                "a zero byte. Then, if synchronization is disrupted on either side the following "
                "algorithm is used:"
                msgstr ""
                "Ни одна команда не начинается нулём ('\\\\\\\\0'). Поэтому возможен такой метод "
                "синхронизации: контроллер на каждый полученный первый байт команды равный нулю "
                "отвечает нулём, а компьютер игнорирует первые байт ответа если он равен нулю и "
                "переходит к рассмотрению следующего. Тогда в случая когда синхронизация нарушена "
                "на стороне компьютера или контроллера, но еще не прошло время таймаута "
                "контроллера, возможен следующий алгоритм:"

                msgid ""
                "In case PC receives \\"errc\\", \\"errd\\" or a wrong command answer code, then PC "
                "sends 4 to 250 zeroes to the controller (250 byte limit is caused by input "
                "buffer length and usage of I2C protocol, less than 4 zeroes do not guarantee "
                "successful resynchronization). During this time PC continuously reads incoming "
                "bytes from the controller until the first zero is received and stops sending and "
                "receiving right after that."
                msgstr ""
                "Если компьютером в ответ на переданную команду с данными или без, получен от "
                "контроллера ответ не на ту команду, \\"errc\\" либо \\"errd\\" , то с компьютера в "
                "контроллер средствами библиотеки посылается от 4 до 250 нулей (ограничение в 250 "
                "байт связано с длиной приёмного буфера и протоколом передачи данных по I2C, а "
                "передача менее 4 нулей часто не приведёт к восстановлению синхронизации). При "
                "этом происходит постоянное считывание приходящих байт от контроллера до "
                "появления первого нуля. После этого и считывание и посылка прекращаются."

                msgid ""
                "Received zero byte is likely not a part of a response to a previous command "
                "because on error PC receives \\"errc\\"/\\"errd\\" response. It is possible in rare "
                "cases, then synchronization procedure will start again. Therefore first zero "
                "byte received by the PC means that controller input buffer is already empty and "
                "will remain so until any command is sent. Right after receiving first zero byte "
                "from the controller PC is ready to transmit next command code. The rest of zero "
                "bytes in transit will be ignored because they will be received before controller "
                "response."
                msgstr ""
                "Принятый нуль обычно не является частью предыдущей передачи, так как в моменты "
                "ошибок контроллер получает ответы \\"errc\\" / \\"errd\\". В редких случаях (особое "
                "изменение байта на стороне контроллера) возможна  синхронизация с некоторой "
                "попытки. Таким образом, приход первого нуля обычно означает, что приёмный буфер "
                "контроллера чист и уже не заполнится, пока не придёт первая значимая команда. "
                "Сразу после прихода первого нуля от контроллера компьютер готов передавать "
                "следующую команду. Остальные нули, находящиеся в пересылке, будут "
                "проигнорированы, так как придут до ответа контроллера."

                msgid "This completes the zero byte synchronization procedure."
                msgstr "Синхронизация завершена."

                msgid "Library-side error processing"
                msgstr "Обработка ошибок на стороне библиотеки"

                msgid "Nearly every library function has a return status of type `result_t`."
                msgstr ""
                "Практически каждая функция библиотеки возвращает статус выполнения типа "
                "`result_t`."

                msgid ""
                "After sending command to the controller library reads incoming bytes until a non-"
                "zero byte is received. All zero bytes are ignored. Library reads first 4 bytes "
                "and compares them to the command code. It then waits for data section and CRC, "
                "if needed. If first 4 received bytes do not match the sent command identifier, "
                "then zero byte synchronization procedure is launched, command is considered to "
                "be sent unsuccessfully. If first 4 received bytes match the sent command "
                "identifier and command has data section, but the received CRC doesn't match CRC "
                "calculated from the received data, then zero byte synchronization procedure is "
                "launched, command is considered to be sent unsuccessfully. If a timeout is "
                "reached while the library is waiting for the controller response, then zero byte "
                "synchronization procedure is launched, command is considered to be sent "
                "unsuccessfully."
                msgstr ""
                "После посылки запроса контроллеру библиотека проверяет первые приходящие байты "
                "пока не встретит первое ненулевое значение. Все нулевые байты игнорируются. "
                "Остальные приходящие байты считаются значимыми. Библиотека ожидает первые 4 "
                "байта ответа. Далее она сравнивает их с кодом запроса и, при необходимости, "
                "ожидает остальные байты пакета данных. Если полученные 4 байта не соответствуют "
                "запросу, то запускается процедура синхронизации очистительными нулями, команда "
                "выполнена неуспешно. Если полученные первые 4 байта совпадают с кодом запроса и "
                "в ответе есть еще данные, то после их получения проверяется CRC код. Если код "
                "неверный, то запускается синхронизация очистительными нулями, выполнение команды "
                "считается неуспешным."

                msgid ""
                "If no errors were detected, then command is considered to be successfully "
                "completed and `result_ok` is returned."
                msgstr ""
                "Если ошибок не обнаружено, то команда считается выполненной успешно и "
                "возвращается `result\\\\_ok`."

                msgid "Library return codes"
                msgstr "Возможные значения ответа библиотеки"

                msgid "`result_ok`. No errors detected."
                msgstr "`result_ok`. Ошибок нет."

                msgid ""
                "`result_error`. Generic error. Can happen because of hardware problems, empty "
                "port buffer, timeout or successfull synchronization after an error. Another "
                "common reason for this error is protocol version mismatch between controller "
                "firmware and PC library."
                msgstr ""
                "`result_error`. Общая ошибка. Может быть связана с аппаратными проблемами, "
                "отсутствием данных в буфере порта, превышением таймаутов. Также может означать "
                "сбой синхронизации, который был устранён. Такой сбой мог быть вызван помехами на "
                "линии связи с контроллером. Еще одной причиной может быть несоответствие "
                "протоколов в прошивке и в контроллере."

                msgid ""
                "`result_nodevice`. Error opening device, lost connection or failed "
                "synchronization. Device reopen and/or user action is required."
                msgstr ""
                "`result_nodevice`. Невозможность открытия устройства, потеря связи с ним в "
                "процессе передачи данных, неудачная синхронизация. Требуется повторное открытие "
                "устройства или вмешательство пользователя."

                msgid ""
                "If a function returns an error values of all parameters it writes to are "
                "undefined. Error code may be accompanied by detailed error description output to "
                "system log (Unix-like OS) or standard error (Windows-like OS)."
                msgstr ""
                "Если функция возвращает ошибку, любые переданные в неё структуры для записи "
                "считаются неопределёнными. Возврат кода ошибки может сопровождаться записью "
                "подробного сообщения в системный лог на unix или в stderr на windows."

                msgid "Zero byte synchronization procedure"
                msgstr "Процедура синхронизации очистительными нулями"

                msgid ""
                "Synchronization is performed by means of sending zero ('\\\\\\\\0') bytes and reading "
                "bytes until a zero byte is received. Optionally one may clear port buffer at the "
                "end of synchronization procedure. Initially 64 zero bytes are sent. If there "
                "were no zero bytes received during the timeout, then a string of 64 bytes is "
                "sent 3 more times. After 4 unsuccessful attempts and no zero bytes received "
                "device is considered lost. In this case library should return `result_nodevice` "
                "error code. In case of successful syncronization library returns `result_error`."
                msgstr ""
                "Восстановление синхронизации осуществляется посылкой нулевых байтов и считывания "
                "принимаемых байт до появления первого нулевого значения ('\\\\\\\\0'). Опционально "
                "можно в конце синхронизации очистить буфер порта. Посылается изначально 64 "
                "нулевых байта. Если от контроллера не пришло ни одного нулевого байта за время "
                "таймаута, то 64 байта посылаются еще 3 раза. После 4 посылки и неполучения "
                "нулевого байта устройство считается потерянным и библиотека должна вернуть код "
                "ошибки `result_nodevice`. В случае удачной синхронизации возвращаемый код ошибки "
                "`result_error`."

                msgid "Controller error response types"
                msgstr "Коды ошибок ответов контроллера"

                msgid "ERRC"
                msgstr "ERRC"

                msgid "**Answer:** (4 bytes)"
                msgstr "**Ответ:** (4 байт)"

                msgid "**Code:** \\"errc\\" or 0x63727265"
                msgstr "Код: \\"errc\\" или 0x63727265"

                msgid "uint32_t"
                msgstr "uint32_t"


                msgid "errc"
                msgstr "errc"

                msgid "Command error"
                msgstr "Команда недоступна"

                msgid "**Description:**"
                msgstr "**Описание**"

                msgid ""
                "Controller answers with \\"errc\\" if the command is either not recognized or "
                "cannot be processed and sets the correspoding bit in status data structure."
                msgstr ""
                "Ответ на команду, в случае если команда неизвестна, либо не может быть выполнена "
                "и/или обработана в данный момент (в данном состоянии). Устанавливает "
                "соответствующий бит в поле \\"flags\\" структуры состояния."

                msgid "ERRD"
                msgstr "ERRD"

                msgid "**Code:** \\"errd\\" or 0x64727265"
                msgstr "Код: \\"errd\\" или 0x64727265"

                msgid "errd"
                msgstr "errd"

                msgid "Data error"
                msgstr "Неверные данные"


                msgid ""
                "Controller answers with \\"errd\\" if the CRC of the data section computed by the "
                "controller doesn't match the received CRC field and sets the correspoding bit in "
                "status data structure."
                msgstr ""
                "Ответ на команду \\"errd\\", устанавливается в том случае, если вычислиные контроллером "
                "данные CRC не совпадают с полученым полем CRC. В этом случае устанавливается бит "
                "соответствия в поле \\"flags\\" структуры состояния."

                msgid "ERRV"
                msgstr "ERRV"

                msgid "**Code:** \\"errv\\" or 0x76727265"
                msgstr "Код: \\"errv\\" или 0x76727265"

                msgid "errv"
                msgstr "errv"

                msgid "Value error"
                msgstr "Неверное значение"

                msgid ""
                "Controller answers with \\"errv\\" if any of the values in the command are out of "
                "acceptable range and can not be applied. Inacceptable value is replaced by a "
                "rounded, truncated or default value. Controller also sets the correspoding bit "
                "in status data structure."
                msgstr ""
                "Ответ на команду, в случае если команда корректна, контрольная сумма правильная, "
                "но передаваемые значения (хотя бы одно из них) выходят за допустимый диапазон и "
                "не могут быть приняты. При этом неверное значение заменяется одним из верных "
                "методами округления, ограничения или сбрасывания в некое стандартное состояние. "
                "Устанавливает соответствующий бит в поле \\"flags\\" структуры состояния."

                msgid "All controller commands"
                msgstr "Все команды контроллера"

               """.format(protocol.version))
    return s[1:]  # remove first line
