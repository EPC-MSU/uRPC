static const char *RcsId = "$Id:  $";
//=============================================================================
//
// file :        ${device_name(protocol)}StateMachine.cpp
//
// description : State machine file for the ${device_name(protocol)} class
//
// project :     StandaTango
//
// This file is part of Tango device class.
// 
// Tango is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// Tango is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
// 
// You should have received a copy of the GNU General Public License
// along with Tango.  If not, see <http://www.gnu.org/licenses/>.
// 
// $Author:  $
//
// $Revision:  $
// $Date:  $
//
// $HeadURL:  $
//
//=============================================================================
//                This file is generated by POGO
//        (Program Obviously used to Generate tango Object)
//=============================================================================

#include "${device_name(protocol)}.h"

//================================================================
//  States  |  Description
//================================================================

<%namespace file="${context['import_file']('Project.h.mako')}" import="validator_decl"/>\
namespace ${device_name(protocol)}_ns {


% for cmd in all_cmds(protocol):
// Command ${cmd.name}
${validator_decl(cmd)}
{
    return true;
}
% endfor
% for arg in all_args_as_attrs(protocol):
${validator_decl(arg)}
{
    return true;
}

% endfor


}	// namespace ${device_name(protocol)}_ns
