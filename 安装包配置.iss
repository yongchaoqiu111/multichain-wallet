; 安装脚本配置
#define MyAppName "演示钱包版本"
#define MyAppVersion "1.0"
#define MyAppPublisher "演示版本"
#define MyAppExeName "多链钱包工具.exe"

[Setup]
AppId={{A8B7C6D5-E4F3-2A1B-0C9D-8E7F6A5B4C3D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=AI656Wallet_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "F:\qianbao\dist\多链钱包工具.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\多链钱包工具.exe"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\多链钱包工具.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\多链钱包工具.exe"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
