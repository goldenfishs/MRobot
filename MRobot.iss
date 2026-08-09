#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#ifndef MyAppArch
  #define MyAppArch "x64"
#endif

[Setup]
AppId={{D7F54C74-3970-4DA4-9C8E-D54A3B770F40}
AppName=MRobot
AppVersion={#MyAppVersion}
AppPublisher=MRobot
AppPublisherURL=https://github.com/goldenfishs/MRobot
DefaultDirName={localappdata}\Programs\MRobot
DefaultGroupName=MRobot
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=release-dist
OutputBaseFilename=MRobot-v{#MyAppVersion}-windows-{#MyAppArch}-setup
SetupIconFile=assets\logo\MRobot.ico
UninstallDisplayIcon={app}\MRobot.exe
Compression=lzma2
SolidCompression=yes
CloseApplications=force
RestartApplications=yes
WizardStyle=modern

[Files]
Source: "dist\MRobot.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\MRobot"; Filename: "{app}\MRobot.exe"
Name: "{autodesktop}\MRobot"; Filename: "{app}\MRobot.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标："; Flags: unchecked

[Run]
Filename: "{app}\MRobot.exe"; Description: "启动 MRobot"; Flags: nowait
