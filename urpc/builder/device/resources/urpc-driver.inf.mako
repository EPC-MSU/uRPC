[Version]
Signature="$Windows NT$"
Class=Ports
ClassGuid={4d36e978-e325-11ce-bfc1-08002be10318}
Provider=%MFGNAME%
LayoutFile=layout.inf
DriverVer=06/21/2006
CatalogFile.NTx86=device_name.cat
CatalogFile.NTamd64=device_name.cat

[DefaultInstall]
CopyINF=device_name.inf

[Manufacturer]
%%MFGNAME%=CommunicationDevice,NT,NTamd64

[CommunicationDevice.NT]
%%DESCR%=DriverInstall,USB\VID_${protocol.vid.replace("0x","")}&PID_${protocol.pid.replace("0x","")}

[CommunicationDevice.NTamd64]
%%DESCR%=DriverInstall,USB\VID_${protocol.vid.replace("0x","")}&PID_${protocol.pid.replace("0x","")}

[DriverInstall]
Include=mdmcpq.inf
CopyFiles=FakeModemCopyFileSection

[DriverInstall.Services]
Include=mdmcpq.inf
AddService=usbser,0x00000002,LowerFilter_Service_Inst

[DriverInstall.HW]
Include=mdmcpq.inf
AddReg=LowerFilterAddReg

[Strings]
MFGNAME="${protocol.manufacturer}"
DESCR="${protocol.product_name} Universal Driver"
