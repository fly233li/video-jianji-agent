; 视频剪辑助手 — Inno Setup 安装脚本
; 用法: ISCC.exe packaging\installer.iss

#define MyAppName "视频剪辑助手"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "小飞龙"
#define MyAppURL "http://localhost:8000"
#define MyAppExeName "VideoEditAgent.exe"

[Setup]
; 基本设置
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/
AppSupportURL=https://github.com/
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist
OutputBaseFilename=视频剪辑助手_v2.0_安装程序
Compression=lzma2/max
SolidCompression=yes

; 图标与安装程序外观
SetupIconFile=..\logo.ico
WizardStyle=modern
WizardSizePercent=120

; 卸载
UninstallDisplayIcon={app}\logo.ico
UninstallDisplayName={#MyAppName}

; 权限管理
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; 其他
AllowNoIcons=yes
ShowLanguageDialog=no
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："; Flags: checkedonce
Name: "firewall"; Description: "添加 Windows 防火墙例外（允许本地访问）"; GroupDescription: "防火墙设置："; Flags: checkedonce

[Files]
; 主程序及所有文件（递归）
Source: "..\dist\视频剪辑助手\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
; 开始菜单
Name: "{autoprograms}\{#MyAppName}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autoprograms}\{#MyAppName}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; 安装完成后可选启动
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent unchecked; WorkingDir: "{app}"

[Code]
// 安装后创建防火墙例外
procedure AddFirewallException(AppPath: string; AppName: string);
var
  ResultCode: Integer;
begin
  Exec('netsh', 'advfirewall firewall add rule name="' + AppName + '" dir=in program="' + AppPath + '" action=allow protocol=tcp localport=8000 description="Video Edit Agent Web Service"',
    '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('firewall') then
    begin
      AddFirewallException(ExpandConstant('{app}\{#MyAppExeName}'), '{#MyAppName}');
    end;
  end;
end;

// 安装成功后的提示
procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpFinished then
  begin
    WizardForm.FinishedLabel.Caption := ExpandConstant('{#MyAppName} 安装完成！' +#13#10+
      '启动后请访问 http://localhost:8000 使用' +#13#10+
      '如需修改配置，请编辑 {app}\config.py');
  end;
end;
