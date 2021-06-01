// file :        ${device_name(protocol)}Config.h

#ifndef ${device_name(protocol)}Config_H
#define ${device_name(protocol)}Config_H


namespace ${device_name(protocol)}_internal_ns {


extern int ${device_name(protocol)}_argc;
extern char **${device_name(protocol)}_argv;

extern char *${device_name(protocol)}_server_name;
extern char *${device_name(protocol)}_instance_name;
extern char *${device_name(protocol)}_class_name;

extern bool ${device_name(protocol)}_reactive_enabled;
extern bool ${device_name(protocol)}_reinit_by_readers_enabled;

extern bool ${device_name(protocol)}_profile_pollers;
extern bool ${device_name(protocol)}_profile_cmd;
extern bool ${device_name(protocol)}_profile_ar;
extern bool ${device_name(protocol)}_profile_aw;


}	// namespace ${device_name(protocol)}_internal_ns


#endif	// ${device_name(protocol)}Config_H
