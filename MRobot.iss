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

[Icons]
Name: "{group}\MRobot"; Filename: "{app}\MRobot.exe"; IconFilename: "{app}\assets\logo\M.ico"
Name: "{userdesktop}\MRobot"; Filename: "{app}\MRobot.exe"; IconFilename: "{app}\assets\logo\M.ico"