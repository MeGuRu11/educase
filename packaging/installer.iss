#ifndef AppVersion
  #error AppVersion must be passed by build_installer.bat
#endif

#define AppName "EpiCase"
#define ConstructorExe "EpiCase Constructor.exe"
#define PlayerExe "EpiCase Player.exe"

[Setup]
AppId={{6A2BBD1B-1646-4D0E-92DB-21BCE0D50322}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=ВМА им. С. М. Кирова
DefaultDirName={autopf}\EpiCase
DefaultGroupName=EpiCase
DisableProgramGroupPage=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
WizardStyle=modern dynamic
ShowLanguageDialog=no
AlwaysShowComponentsList=yes
ShowComponentSizes=yes
OutputDir=..\dist
OutputBaseFilename=EpiCase Installer {#AppVersion}
Compression=lzma2/max
SolidCompression=yes
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
UsePreviousSetupType=no
UsePreviousTasks=yes
UninstallDisplayName=EpiCase
VersionInfoVersion={#AppVersion}
VersionInfoProductVersion={#AppVersion}
VersionInfoTextVersion={#AppVersion}
VersionInfoProductName=EpiCase
VersionInfoDescription=EpiCase Installer

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Types]
Name: "full"; Description: "Constructor и Player"
Name: "constructor"; Description: "Только Constructor"
Name: "player"; Description: "Только Player"

[Components]
Name: "constructor"; Description: "EpiCase Constructor"; Types: full constructor; Flags: disablenouninstallwarning
Name: "player"; Description: "EpiCase Player"; Types: full player; Flags: disablenouninstallwarning

[Tasks]
Name: "desktopicon"; Description: "Создать ярлыки на рабочем столе"; GroupDescription: "Дополнительные ярлыки:"; Flags: unchecked

[Files]
Source: "..\dist\EpiCase Constructor.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: constructor
Source: "..\dist\EpiCase Player.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: player

[Icons]
Name: "{group}\EpiCase Constructor"; Filename: "{app}\{#ConstructorExe}"; WorkingDir: "{app}"; Components: constructor
Name: "{group}\EpiCase Player"; Filename: "{app}\{#PlayerExe}"; WorkingDir: "{app}"; Components: player
Name: "{commondesktop}\EpiCase Constructor"; Filename: "{app}\{#ConstructorExe}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: constructor
Name: "{commondesktop}\EpiCase Player"; Filename: "{app}\{#PlayerExe}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: player

[InstallDelete]
Type: files; Name: "{app}\{#ConstructorExe}"; Check: not WizardIsComponentSelected('constructor')
Type: files; Name: "{group}\EpiCase Constructor.lnk"; Check: not WizardIsComponentSelected('constructor')
Type: files; Name: "{commondesktop}\EpiCase Constructor.lnk"; Check: not WizardIsComponentSelected('constructor')
Type: files; Name: "{app}\{#PlayerExe}"; Check: not WizardIsComponentSelected('player')
Type: files; Name: "{group}\EpiCase Player.lnk"; Check: not WizardIsComponentSelected('player')
Type: files; Name: "{commondesktop}\EpiCase Player.lnk"; Check: not WizardIsComponentSelected('player')
