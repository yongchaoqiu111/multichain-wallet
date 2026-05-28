; Inno Setup 脚本 - 钱包应用安装包
[Setup]
AppName=AI656 钱包
AppVersion=1.0
DefaultDirName={pf}\AI656Wallet
DefaultGroupName=AI656 钱包
OutputDir=output
OutputBaseFilename=AI656Wallet_Setup
SetupIconFile=ClientWallet2026SecureKey32B!!!!.ico
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "desktop\dist\多链钱包工具.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\AI656 钱包"; Filename: "{app}\多链钱包工具.exe"
Name: "{commondesktop}\AI656 钱包"; Filename: "{app}\多链钱包工具.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "其他选项:"; Flags: unchecked

[Run]
Filename: "{app}\多链钱包工具.exe"; Description: "运行 AI656 钱包"; Flags: nowait postinstall skipifsilent
