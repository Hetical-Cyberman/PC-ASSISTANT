[Setup]
AppId={{A8A8E7A6-7C7A-4E7D-B8D8-7D5F2F2D8D18}}
AppName=Cyberman
AppVersion=0.1.0
AppPublisher=Cyberman
DefaultDirName={autopf}\Cyberman
DefaultGroupName=Cyberman
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=Cyberman-Setup
SetupIconFile=..\assets\cyberman.ico
UninstallDisplayIcon={app}\Cyberman.exe
Compression=lzma
SolidCompression=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "..\dist\Cyberman\Cyberman.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Cyberman"; Filename: "{app}\Cyberman.exe"
Name: "{autodesktop}\Cyberman"; Filename: "{app}\Cyberman.exe"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\Cyberman.exe"; Description: "Launch Cyberman"; Flags: nowait postinstall skipifsilent


