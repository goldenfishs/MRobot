[Setup]
AppName=MRobot
AppVersion=1.1.0
DefaultDirName={userappdata}\MRobot
DefaultGroupName=MRobot
OutputDir=.
OutputBaseFilename=MRobotInstaller

[Files]
; 复制整个 dist\MRobot 文件夹（onedir 模式生成的所有文件）
Source: "dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
; 复制 assets 资源文件到安装目录（支持后续更新）
Source: "assets\logo\*"; DestDir: "{app}\assets\logo"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\MRobot"; Filename: "{app}\MRobot.exe"; IconFilename: "{app}\assets\logo\M.ico"
Name: "{userdesktop}\MRobot"; Filename: "{app}\MRobot.exe"; IconFilename: "{app}\assets\logo\M.ico"