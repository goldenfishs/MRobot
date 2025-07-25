[Setup]
AppName=MRobot
AppVersion=1.0.1
DefaultDirName={userappdata}\MRobot
DefaultGroupName=MRobot
OutputDir=.
OutputBaseFilename=MRobotInstaller

[Files]
Source: "dist\MRobot.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\logo\*"; DestDir: "{app}\assets\logo"; Flags: ignoreversion recursesubdirs
Source: "assets\User_code\*"; DestDir: "{app}\assets\User_code"; Flags: ignoreversion recursesubdirs
Source: "assets\mech_lib\*"; DestDir: "{app}\assets\mech_lib"; Flags: ignoreversion recursesubdirs
Source: "assets\logo\M.ico"; DestDir: "{app}\assets\logo"; Flags: ignoreversion

[Icons]
Name: "{group}\MRobot"; Filename: "{app}\MRobot.exe"; IconFilename: "{app}\assets\logo\M.ico"
Name: "{userdesktop}\MRobot"; Filename: "{app}\MRobot.exe"; IconFilename: "{app}\assets\logo\M.ico"