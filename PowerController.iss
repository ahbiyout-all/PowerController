; ===============================================================================
; PowerController - Inno Setup 6 Compiler Script
; Smart Shutdown Agent & Auto Power Manager
; Publisher: AhBiYout | Developer: AhBiYout
; ===============================================================================

#ifndef MyAppVersion
#define MyAppVersion "2.9.1"
#endif

#define MyAppName "PowerController"
#define MyAppPublisher "AhBiYout"
#define MyAppURL "https://ahbiyoutvibe.blogspot.com/"
#define MyAppExeName "PowerController.exe"
#define MyAppMutex "Global\PowerControllerSingleInstanceMutex_f8908445,PowerController_SingleInstance_Mutex"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
AppId={{5A8C9B23-7F12-4D39-8C92-E6B3C0F59871}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=docs\LICENSE_ko.txt
OutputDir=dist
OutputBaseFilename=PowerController_Setup_v{#MyAppVersion}
SetupIconFile=PowerController.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
CloseApplications=force
RestartApplications=no
CloseApplicationsFilter=*.exe
AppMutex={#MyAppMutex}
ArchitecturesInstallIn64BitMode=x64compatible

; ===============================================================================
; Windows File Properties (속성 > 자세히 탭) 메타데이터 설정
; ===============================================================================
VersionInfoVersion={#MyAppVersion}.0
VersionInfoTextVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription=PowerController - 스마트 시스템 전원 및 자동 종료 예약 제어기 설치 마법사
VersionInfoCopyright=Copyright (c) 2026 AhBiYout. All rights reserved.
VersionInfoProductName={#MyAppName} - Smart Shutdown Agent
VersionInfoProductVersion={#MyAppVersion}.0
VersionInfoProductTextVersion={#MyAppVersion}
VersionInfoOriginalFileName=PowerController_Setup_v{#MyAppVersion}.exe

[Languages]
Name: "korean"; MessagesFile: "compiler:Languages\Korean.isl"; LicenseFile: "docs\LICENSE_ko.txt"
Name: "english"; MessagesFile: "compiler:Default.isl"; LicenseFile: "docs\LICENSE_en.txt"

[CustomMessages]
korean.CreateDesktopIcon=바탕 화면에 바로가기 아이콘 생성(&D)
korean.CreateStartupIcon=Windows 시작 시 자동 실행 등록(&S)
korean.LaunchProgram=PowerController 지금 바로 실행하기(&R)
korean.AdditionalTasksGroup=추가 작업 선택:
english.CreateDesktopIcon=Create a &desktop shortcut
english.CreateStartupIcon=Register to start automatically with &Windows
english.LaunchProgram=Launch PowerController now
english.AdditionalTasksGroup=Additional shortcuts:

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalTasksGroup}"
Name: "startupicon"; Description: "{cm:CreateStartupIcon}"; GroupDescription: "{cm:AdditionalTasksGroup}"; Flags: unchecked

[Files]
; -------------------------------------------------------------------------------
; 1. Unpacked Multi-File distribution (PyInstaller --onedir 폴더 풀림 개별 파일 및 내부 디렉터리 트리 일체)
; -------------------------------------------------------------------------------
Source: "dist\PowerController\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; -------------------------------------------------------------------------------
; 2. Standalone Executable Binaries (단일 파일 빌드 모드 지원)
; -------------------------------------------------------------------------------
Source: "dist\PowerController.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\PowerNetworkScheduler\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist
Source: "dist\PowerNetworkScheduler.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "dist\ApplySharedSchedules.exe"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

; -------------------------------------------------------------------------------
; 3. Companion Tools, Native DLLs, Configuration Scripts, Assets & Documentation Multi-Files
; -------------------------------------------------------------------------------
Source: "PowerCoreNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "NetBeaconEngine.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "FirewallNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "SysPowerHook.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "ScheduleCrypto.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "native_bridge.py"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "schedule_share_builder.py"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Register_Firewall_Rules.bat"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "PowerController.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "PowerController.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "docs\*"; DestDir: "{app}\docs"; Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\PowerController.ico"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\PowerController.ico"; Tasks: desktopicon
Name: "{autostartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Parameters: "--startup --tray"; Tasks: startupicon

[Run]
; -------------------------------------------------------------------------------
; 1. Windows Defender Firewall 사전 무음 등록 (메인 & 커맨더 관리 타워)
;    - 기본 앱 이름 및 버전 정보가 포함된 이름(v{#MyAppVersion})으로 인바운드/아웃바운드 동시 등록
;    - 설치 시 관리자 권한으로 사전 등록하여 '공용 네트워크 액세스 허용' 팝업 원천 차단
; -------------------------------------------------------------------------------
; [메인 앱 - PowerController.exe (기본 규칙 및 버전 표기 규칙)]
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController (Inbound)"" dir=in action=allow program=""{app}\{#MyAppExeName}"" enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController (Outbound)"" dir=out action=allow program=""{app}\{#MyAppExeName}"" enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController v{#MyAppVersion} (Inbound)"" dir=in action=allow program=""{app}\{#MyAppExeName}"" enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController v{#MyAppVersion} (Outbound)"" dir=out action=allow program=""{app}\{#MyAppExeName}"" enable=yes profile=any"; Flags: runhidden

; [커맨더 앱 - PowerNetworkScheduler.exe (기본 규칙 및 버전 표기 규칙)]
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerNetworkScheduler (Inbound)"" dir=in action=allow program=""{app}\PowerNetworkScheduler.exe"" enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerNetworkScheduler (Outbound)"" dir=out action=allow program=""{app}\PowerNetworkScheduler.exe"" enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerNetworkScheduler v{#MyAppVersion} (Inbound)"" dir=in action=allow program=""{app}\PowerNetworkScheduler.exe"" enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerNetworkScheduler v{#MyAppVersion} (Outbound)"" dir=out action=allow program=""{app}\PowerNetworkScheduler.exe"" enable=yes profile=any"; Flags: runhidden

; [원격 수신 및 통신 포트 허용 (TCP 9988, UDP 9985, UDP 9986)]
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController TCP 9988"" dir=in action=allow protocol=TCP localport=9988 enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController UDP 9985"" dir=in action=allow protocol=UDP localport=9985 enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController UDP 9986"" dir=in action=allow protocol=UDP localport=9986 enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController v{#MyAppVersion} TCP 9988"" dir=in action=allow protocol=TCP localport=9988 enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController v{#MyAppVersion} UDP 9985"" dir=in action=allow protocol=UDP localport=9985 enable=yes profile=any"; Flags: runhidden
Filename: "netsh"; Parameters: "advfirewall firewall add rule name=""PowerController v{#MyAppVersion} UDP 9986"" dir=in action=allow protocol=UDP localport=9986 enable=yes profile=any"; Flags: runhidden

; 프로그램 바로 실행 옵션
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; 프로그램 삭제 시 등록된 방화벽 규칙 모두 정리 (기본 및 버전 표기 규칙, RunOnceId 지정으로 재실행 중복 방지 및 컴파일 경고 제거)
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController (Inbound)"""; Flags: runhidden; RunOnceId: "DelFwRulePCI"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController (Outbound)"""; Flags: runhidden; RunOnceId: "DelFwRulePCO"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController v{#MyAppVersion} (Inbound)"""; Flags: runhidden; RunOnceId: "DelFwRulePCVerI"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController v{#MyAppVersion} (Outbound)"""; Flags: runhidden; RunOnceId: "DelFwRulePCVerO"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerNetworkScheduler (Inbound)"""; Flags: runhidden; RunOnceId: "DelFwRulePNSI"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerNetworkScheduler (Outbound)"""; Flags: runhidden; RunOnceId: "DelFwRulePNSO"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerNetworkScheduler v{#MyAppVersion} (Inbound)"""; Flags: runhidden; RunOnceId: "DelFwRulePNSVerI"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerNetworkScheduler v{#MyAppVersion} (Outbound)"""; Flags: runhidden; RunOnceId: "DelFwRulePNSVerO"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController TCP 9988"""; Flags: runhidden; RunOnceId: "DelFwRulePortTCP"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController UDP 9985"""; Flags: runhidden; RunOnceId: "DelFwRulePortUDP"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController UDP 9986"""; Flags: runhidden; RunOnceId: "DelFwRulePortUDP9986"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController v{#MyAppVersion} TCP 9988"""; Flags: runhidden; RunOnceId: "DelFwRulePortVerTCP"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController v{#MyAppVersion} UDP 9985"""; Flags: runhidden; RunOnceId: "DelFwRulePortVerUDP"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController v{#MyAppVersion} UDP 9986"""; Flags: runhidden; RunOnceId: "DelFwRulePortVerUDP9986"
Filename: "netsh"; Parameters: "advfirewall firewall delete rule name=""PowerController"""; Flags: runhidden; RunOnceId: "DelFwRuleLegacyPC"

[UninstallDelete]
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.tmp"
Type: files; Name: "{app}\*.old_*"
Type: dirifempty; Name: "{app}"

[Code]
// ===============================================================================
// 기존 실행 중인 프로세스 강제 종료 및 파일 락 즉시 해제 (무인/원격 설치 멈춤 원천 방지)
// ===============================================================================
procedure ForceKillProcess(const ExeName: String);
var
  ResultCode: Integer;
  BaseName: String;
begin
  BaseName := ChangeFileExt(ExeName, '');
  // 1. taskkill /F /T 트리 강제 종료 (최상위 및 모든 자식 프로세스 포함)
  Exec(ExpandConstant('{cmd}'), '/c taskkill.exe /F /T /IM "' + ExeName + '" >nul 2>&1', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  
  // 2. PowerShell Stop-Process 보조 강제 종료
  Exec('powershell.exe', '-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command "Get-Process -Name ''' + BaseName + ''' -ErrorAction SilentlyContinue | Stop-Process -Force"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);

  // 3. WMIC 프로세스 강제 종료 (사내 보안 정책으로 파워쉘 차단 환경 대비)
  Exec(ExpandConstant('{cmd}'), '/c wmic process where "name=''' + ExeName + '''" call terminate >nul 2>&1', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure KillAllPowerProcesses();
begin
  ForceKillProcess('PowerController.exe');
  ForceKillProcess('PowerNetworkScheduler.exe');
  ForceKillProcess('ApplySharedSchedules.exe');
end;

procedure UnlockFileLock(const TargetExe: String);
var
  I: Integer;
  TempOldFile: String;
begin
  if not FileExists(TargetExe) then
    Exit;

  for I := 1 to 15 do
  begin
    TempOldFile := TargetExe + '.old_' + IntToStr(I);
    if FileExists(TempOldFile) then
      DeleteFile(TempOldFile);

    if RenameFile(TargetExe, TempOldFile) then
    begin
      DeleteFile(TempOldFile);
      Break;
    end;
    Sleep(150);
  end;
end;

procedure UnlockDirectoryBinaries(const TargetDir: String);
begin
  if (TargetDir = '') or (not DirExists(TargetDir)) then
    Exit;

  UnlockFileLock(AddBackslash(TargetDir) + '{#MyAppExeName}');
  UnlockFileLock(AddBackslash(TargetDir) + 'PowerNetworkScheduler.exe');
  UnlockFileLock(AddBackslash(TargetDir) + 'ApplySharedSchedules.exe');
end;

// 레지스트리 및 기본 시스템 경로에서 기존 설치 디렉터리 안전 조회 ({app} 상수 미사용)
function GetInstalledPath(): String;
var
  RegKey: String;
begin
  Result := '';
  // 1. AppId 기반 레지스트리 확인
  RegKey := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{5A8C9B23-7F12-4D39-8C92-E6B3C0F59871}_is1';
  if not RegQueryStringValue(HKLM, RegKey, 'Inno Setup: App Path', Result) then
    if not RegQueryStringValue(HKCU, RegKey, 'Inno Setup: App Path', Result) then
    begin
      // 2. 레거시 AppName 기반 레지스트리 확인
      RegKey := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1';
      if not RegQueryStringValue(HKLM, RegKey, 'Inno Setup: App Path', Result) then
        if not RegQueryStringValue(HKCU, RegKey, 'Inno Setup: App Path', Result) then
        begin
          // 3. 기본 Program Files 경로 폴백
          if DirExists(ExpandConstant('{autopf}\{#MyAppName}')) then
            Result := ExpandConstant('{autopf}\{#MyAppName}');
        end;
    end;
end;

// ===============================================================================
// 방화벽 규칙 사전 무음 등록 및 정리 헬퍼 (메인 및 커맨더 2개 모두 + 버전 정보 포함)
// ===============================================================================
procedure SilentExec(const CommandLine: String);
var
  ResultCode: Integer;
begin
  Exec(ExpandConstant('{cmd}'), '/c ' + CommandLine, '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure RegisterFirewallRulesSilently();
var
  AppDir, MainExe, SchedExe, Ver: String;
begin
  AppDir := ExpandConstant('{app}');
  MainExe := AddBackslash(AppDir) + '{#MyAppExeName}';
  SchedExe := AddBackslash(AppDir) + 'PowerNetworkScheduler.exe';
  Ver := '{#MyAppVersion}';

  // 1. 기존 동명 규칙 사전 정리 (중복 생성 방지)
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController (Inbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController (Outbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' (Inbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' (Outbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController" >nul 2>&1');

  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerNetworkScheduler (Inbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerNetworkScheduler (Outbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerNetworkScheduler v' + Ver + ' (Inbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerNetworkScheduler v' + Ver + ' (Outbound)" >nul 2>&1');

  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController TCP 9988" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController UDP 9985" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController UDP 9986" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' TCP 9988" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' UDP 9985" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' UDP 9986" >nul 2>&1');

  // 2. 메인 프로그램 (PowerController.exe) 규칙 사전 등록 (기본 및 버전 표기 규칙 모두 등록)
  if FileExists(MainExe) then
  begin
    SilentExec('netsh.exe advfirewall firewall add rule name="PowerController (Inbound)" dir=in action=allow program="' + MainExe + '" enable=yes profile=any >nul 2>&1');
    SilentExec('netsh.exe advfirewall firewall add rule name="PowerController (Outbound)" dir=out action=allow program="' + MainExe + '" enable=yes profile=any >nul 2>&1');
    SilentExec('netsh.exe advfirewall firewall add rule name="PowerController v' + Ver + ' (Inbound)" dir=in action=allow program="' + MainExe + '" enable=yes profile=any >nul 2>&1');
    SilentExec('netsh.exe advfirewall firewall add rule name="PowerController v' + Ver + ' (Outbound)" dir=out action=allow program="' + MainExe + '" enable=yes profile=any >nul 2>&1');
  end;

  // 3. 커맨더 관리 도구 (PowerNetworkScheduler.exe) 규칙 사전 등록 (기본 및 버전 표기 규칙 모두 등록)
  if FileExists(SchedExe) then
  begin
    SilentExec('netsh.exe advfirewall firewall add rule name="PowerNetworkScheduler (Inbound)" dir=in action=allow program="' + SchedExe + '" enable=yes profile=any >nul 2>&1');
    SilentExec('netsh.exe advfirewall firewall add rule name="PowerNetworkScheduler (Outbound)" dir=out action=allow program="' + SchedExe + '" enable=yes profile=any >nul 2>&1');
    SilentExec('netsh.exe advfirewall firewall add rule name="PowerNetworkScheduler v' + Ver + ' (Inbound)" dir=in action=allow program="' + SchedExe + '" enable=yes profile=any >nul 2>&1');
    SilentExec('netsh.exe advfirewall firewall add rule name="PowerNetworkScheduler v' + Ver + ' (Outbound)" dir=out action=allow program="' + SchedExe + '" enable=yes profile=any >nul 2>&1');
  end;

  // 4. 전용 통신 포트 규칙 사전 등록 (TCP 9988, UDP 9985, UDP 9986 - 기본 및 버전 표기)
  SilentExec('netsh.exe advfirewall firewall add rule name="PowerController TCP 9988" dir=in action=allow protocol=TCP localport=9988 enable=yes profile=any >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall add rule name="PowerController UDP 9985" dir=in action=allow protocol=UDP localport=9985 enable=yes profile=any >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall add rule name="PowerController UDP 9986" dir=in action=allow protocol=UDP localport=9986 enable=yes profile=any >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall add rule name="PowerController v' + Ver + ' TCP 9988" dir=in action=allow protocol=TCP localport=9988 enable=yes profile=any >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall add rule name="PowerController v' + Ver + ' UDP 9985" dir=in action=allow protocol=UDP localport=9985 enable=yes profile=any >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall add rule name="PowerController v' + Ver + ' UDP 9986" dir=in action=allow protocol=UDP localport=9986 enable=yes profile=any >nul 2>&1');
end;

procedure RemoveFirewallRulesSilently();
var
  Ver: String;
begin
  Ver := '{#MyAppVersion}';
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController (Inbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController (Outbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' (Inbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' (Outbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController" >nul 2>&1');

  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerNetworkScheduler (Inbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerNetworkScheduler (Outbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerNetworkScheduler v' + Ver + ' (Inbound)" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerNetworkScheduler v' + Ver + ' (Outbound)" >nul 2>&1');

  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController TCP 9988" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController UDP 9985" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController UDP 9986" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' TCP 9988" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' UDP 9985" >nul 2>&1');
  SilentExec('netsh.exe advfirewall firewall delete rule name="PowerController v' + Ver + ' UDP 9986" >nul 2>&1');
end;

var
  CleanInstallSelected: Boolean;

function InitializeSetup(): Boolean;
var
  PrevPath, UninstExe: String;
  PromptMsg: String;
  UserChoice, ResultCode: Integer;
begin
  Result := True;
  CleanInstallSelected := False;

  // 1. 설치 마법사 시작 전 실행 중인 모든 프로세스 강제 종료 ({app} 상수 절대 미사용)
  KillAllPowerProcesses();

  // 2. 기존 설치 디렉터리가 감지될 경우 처리
  PrevPath := GetInstalledPath();
  if (PrevPath <> '') and DirExists(PrevPath) then
  begin
    UnlockDirectoryBinaries(PrevPath);

    // 대화형(GUI) 모드: 사용자에게 삭제(클린 설치) 또는 덮어쓰기(업그레이드) 선택 질의
    if not WizardSilent() then
    begin
      PromptMsg := 
        '⚠️ [기존 버전 설치 감지 / Existing Version Detected]' + #13#10#13#10 +
        '시스템에 이미 설치된 PowerController가 감지되었습니다.' + #13#10 +
        '  ▶ 설치 경로: ' + PrevPath + #13#10#13#10 +
        '기존 버전을 먼저 완전히 삭제하고 새로 설치(클린 설치)하시겠습니까?' + #13#10#13#10 +
        '  • [예 (Yes)]    : 기존 버전을 안전하게 삭제 후 클린 설치 (Clean Install, 권장)' + #13#10 +
        '  • [아니오 (No)] : 기존 설정 및 파일 위에 덮어쓰기/업그레이드 설치 (Overwrite/Upgrade)' + #13#10 +
        '  • [취소 (Cancel)]: 설치 마법사 종료' + #13#10#13#10 +
        '------------------------------------------------------------' + #13#10 +
        'Do you want to completely uninstall the previous version before installing?';

      UserChoice := MsgBox(PromptMsg, mbConfirmation, MB_YESNOCANCEL);
      if UserChoice = IDYES then
      begin
        CleanInstallSelected := True;
      end
      else if UserChoice = IDCANCEL then
      begin
        Result := False;
        Exit;
      end;
      // IDNO 선택 시: CleanInstallSelected := False 유지하며 기존 파일 위에 덮어쓰기 진행
    end
    else
    begin
      // 무인 설치(Silent / VerySilent) 모드인 경우:
      // 커맨드라인 스위치 /CLEAN 또는 /CLEANINSTALL 이 전달된 경우에만 삭제 후 재설치 진행
      // 기본값은 시스템 관리자 원격 배포에 안전한 무중단 덮어쓰기/업그레이드(Overwrite)
      if (ExpandConstant('{param:clean|0}') = '1') or (ExpandConstant('{param:cleaninstall|0}') = '1') then
        CleanInstallSelected := True;
    end;

    // 클린 설치(삭제) 모드 선택된 경우 기존 언인스톨러 조용히 실행
    if CleanInstallSelected then
    begin
      UninstExe := AddBackslash(PrevPath) + 'unins000.exe';
      if not FileExists(UninstExe) then
        UninstExe := AddBackslash(PrevPath) + 'unins001.exe';

      if FileExists(UninstExe) then
      begin
        Exec(UninstExe, '/SILENT /VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        Sleep(800);
      end;
      UnlockDirectoryBinaries(PrevPath);
    end;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  TargetDir, PromptMsg: String;
  UserChoice: Integer;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    TargetDir := WizardDirValue;
    // 이전에 InitializeSetup에서 이미 클린 처리하지 않았고, 선택한 디렉토리에 기존 실행파일이 존재하는 경우
    if (not CleanInstallSelected) and DirExists(TargetDir) and FileExists(AddBackslash(TargetDir) + '{#MyAppExeName}') then
    begin
      PromptMsg := 
        '선택하신 폴더에 이미 PowerController 프로그램 파일이 존재합니다.' + #13#10#13#10 +
        '  ▶ 대상 경로: ' + TargetDir + #13#10#13#10 +
        '해당 폴더에 기존 파일을 덮어쓰기(업그레이드)하여 설치를 계속하시겠습니까?' + #13#10#13#10 +
        '  • [확인 (OK)]  : 기존 파일 위에 덮어쓰기 계속' + #13#10 +
        '  • [취소 (Cancel)]: 다른 폴더 선택으로 돌아가기';
      UserChoice := MsgBox(PromptMsg, mbConfirmation, MB_OKCANCEL);
      if UserChoice <> IDOK then
      begin
        Result := False;
        Exit;
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // 파일 복사(추출) 직전(ssInstall) 단계: 사용자가 설치 폴더를 확정한 시점이므로 {app} 상수가 100% 안전하게 초기화됨
  if CurStep = ssInstall then
  begin
    KillAllPowerProcesses();
    UnlockDirectoryBinaries(ExpandConstant('{app}'));
  end
  // 파일 추출 직후 및 프로그램 실행 전(ssPostInstall) 단계:
  // 설치 프로그램(Installer)에서 방화벽 규칙을 사전에 조용히 등록 (메인 및 커맨더 2개 모두 + 버전 정보가 붙은 앱 이름도 등록)
  else if CurStep = ssPostInstall then
  begin
    RegisterFirewallRulesSilently();
  end;
end;

function InitializeUninstall(): Boolean;
begin
  // 언인스톨 시작 시에는 {app} 상수가 이미 초기화되어 있으므로 안전하게 호출 가능
  KillAllPowerProcesses();
  UnlockDirectoryBinaries(ExpandConstant('{app}'));
  Result := True;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    KillAllPowerProcesses();
    UnlockDirectoryBinaries(ExpandConstant('{app}'));
  end
  else if CurUninstallStep = usPostUninstall then
  begin
    // 언인스톨 완료 후 잔류 방화벽 규칙 모두 소거
    RemoveFirewallRulesSilently();
  end;
end;
