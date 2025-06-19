[Setup]
AppName=MRobot
AppVersion=1.0.1
DefaultDirName={userappdata}\MRobot
DefaultGroupName=MRobot
OutputDir=.
OutputBaseFilename=MRobotInstaller

[Files]
Source: "dist\MRobot.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "img\*"; DestDir: "{app}\img"; Flags: ignoreversion recursesubdirs
Source: "User_code\*"; DestDir: "{app}\User_code"; Flags: ignoreversion recursesubdirs
Source: "mech_lib\*"; DestDir: "{app}\mech_lib"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\MRobot"; Filename: "{app}\MRobot.exe"; IconFilename: "{app}\img\M.ico"
Name: "{userdesktop}\MRobot"; Filename: "{app}\MRobot.exe"; IconFilename: "{app}\img\M.ico"