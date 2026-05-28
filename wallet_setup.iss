[Setup]
AppName=Multi-Chain Wallet
AppVersion=1.0
DefaultDirName={pf}\MultiChainWallet
DefaultGroupName=Multi-Chain Wallet
OutputDir=.\installer
OutputBaseFilename=MultiChainWallet_Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Files]
Source: "dist\WalletApp\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\钱包应用"; Filename: "{app}\WalletApp.exe"
Name: "{commondesktop}\钱包应用"; Filename: "{app}\WalletApp.exe"

[Run]
Filename: "{app}\WalletApp.exe"; Description: "启动钱包"; Flags: nowait postinstall skipifsilent