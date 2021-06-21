<%namespace import="namespaced" module = "urpc.builder.device.utils.namespaced" inheritable="True"/>\
#ifndef _COMMANDS_H
#define _COMMANDS_H

/*
 * This file is autogenerated.
 * Changes made to this file can be overwritten.
 */

#if defined(__cplusplus)
extern "C"
{
#endif

#pragma pack(push, 1)

/*
 * Protocol version
 */
#define PROTOCOL_VERSION ${view.version}
#define PROTOCOL_VERSION_Q "${view.version}"

/*
 * Command codes.
 */
% for name, value in view.command_codes:
#define ${namespaced(name)}  ${value}
% endfor

/*
 * ERRC, ERRD, ERRV codes must be always
 */
#define ERRC_CMD  0x63727265
#define ERRD_CMD  0x64727265
#define ERRV_CMD  0x76727265

/*
 * All command flags below.
 */

% for flagset in view.flagsets:
/**
* @anchor ${flagset.name}
*/
//@{
% for name, value, description in flagset.members:
    #define ${namespaced(name)}    ${value} /**< \~english ${description["english"]} \~russian ${description["russian"]} */
% endfor
//@}
% endfor

/*
 * All structures below.
 */
% for struct in view.argstructs:
typedef struct
{
  % for decl, description in struct.members:
  ${decl}; /**< \~english ${description["english"]} \~russian ${description["russian"]} */
  % endfor

} ${namespaced(struct.name)};

% endfor
#pragma pack(pop)

%if view.accessors_count():
/*
 * This structure is for storage all accessors parameters.
 */
typedef struct
{
  /*
   * Accessors structures only.
   */
% for (struct_type, struct_code) in view.accessor_argstructs:
  ${namespaced(struct_type)} ${struct_code};
% endfor

} ${namespaced("settings_storage_t")};

extern ${namespaced("settings_storage_t")} Commands_SettingsStorage;

%endif
extern uint16_t Commands_GetInputSize(uint32_t cmd);
extern uint16_t Commands_GetOutputSize(uint32_t cmd);

#if defined(__cplusplus)
};
#endif

#endif  // _COMMANDS_H
