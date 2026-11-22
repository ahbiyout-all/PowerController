; ===============================================================================
; PowerController - Inno Setup 6 Compiler Script
; Smart Shutdown Agent & Auto Power Manager
; Publisher: AhBiYout | Developer: AhBiYout
; ===============================================================================

#ifndef MyAppVersion
#define MyAppVersion "2.9.2"
#endif

#define MyAppName "PowerController"
#define MyAppPublisher "AhBiYout"
#define MyAppURL "https://ahbiyoutvibe.blogspot.com/"
#define MyAppExeName "PowerController.exe"
#define MyAppMutex "Global\PowerControllerSingleInstanceMutex_f8908445,PowerController_SingleInstance_Mutex"

[Setup]
; NOTE: The value of AppId uniquely identifies this application in Windows Add/Remove Programs.
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
DisableProgramGroupPage=yes
AllowNoIcons=yes
LicenseFile=docs\LICENSE_ko.txt
OutputDir=dist
OutputBaseFilename=PowerController_Setup_v{#MyAppVersion}
SetupIconFile=PowerController.ico
; Windows 프로그램 추가/제거(제어판/설정) 정식 등록 지시어
Uninstallable=yes
CreateUninstallRegKey=yes
UninstallDisplayName={#MyAppName} v{#MyAppVersion}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallFilesDir={app}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
LanguageDetectionMethod=uilanguage
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
; AppMutex 대신 InitializeSetup/InitializeUninstall 강제 종료 + Restart Manager 조합을 사용하여
; 실행 중인 기존 앱을 사용자 개입 없이 즉시 자동 종료하고 설치 마법사를 바로 진행합니다.
CloseApplications=force
RestartApplications=no
CloseApplicationsFilter=*.exe
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
; 3. Companion Tools, Native DLLs, Configuration Scripts, Assets & License Files
; (불필요한 개발용 문서 및 포터블 파일 제외, 순수 필수 파일만 배포)
; -------------------------------------------------------------------------------
Source: "PowerCoreNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "NetBeaconEngine.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "FirewallNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "SysPowerHook.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "ScheduleCrypto.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "DiskFlushNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "AudioDimmerNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "DisplayDdcNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "LowLevelInputIdleNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "CommanderTcpDispatcherNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "CommanderPingScannerNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "PowerExecNative.dll"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "native_bridge.py"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "schedule_share_builder.py"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "Register_Firewall_Rules.bat"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "PowerController.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "PowerController.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "docs\LICENSE_ko.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "docs\LICENSE_en.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

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

; 프로그램 바로 실행 옵션 (완료 페이지 체크박스)
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
Type: files; Name: "{autodesktop}\{#MyAppName}.lnk"
Type: files; Name: "{userdesktop}\{#MyAppName}.lnk"
Type: files; Name: "{app}\*.log"
Type: files; Name: "{app}\*.tmp"
Type: files; Name: "{app}\*.old_*"
Type: dirifempty; Name: "{app}"

[Code]
var
  CleanInstallSelected: Boolean;
  DesktopShortcutCheck: TNewCheckBox;
  FinishedLayoutAdjusted: Boolean;

function IsKoreanUI(): Boolean;
begin
  Result := (ActiveLanguage = 'korean');
end;

// ===============================================================================
// 1단계: 기존 실행 중인 프로세스 강제 종료 및 파일 락 즉시 해제
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
  Sleep(250);
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

function QueryUninstallPath(const RootKey: Integer; const SubKey: String; var OutPath, OutUninst: String): Boolean;
begin
  Result := False;
  OutPath := '';
  OutUninst := '';

  if not RegKeyExists(RootKey, SubKey) then
    Exit;

  if not RegQueryStringValue(RootKey, SubKey, 'Inno Setup: App Path', OutPath) then
    RegQueryStringValue(RootKey, SubKey, 'InstallLocation', OutPath);

  if not RegQueryStringValue(RootKey, SubKey, 'QuietUninstallString', OutUninst) then
    RegQueryStringValue(RootKey, SubKey, 'UninstallString', OutUninst);

  if (OutPath = '') and (OutUninst <> '') then
    OutPath := ExtractFileDir(RemoveQuotes(OutUninst));

  Result := (OutPath <> '') or (OutUninst <> '');
end;

// 레지스트리(현재/레거시 Inno/레거시 Python) 및 기본 시스템 경로에서 기존 설치 디렉터리 안전 조회
function GetExistingInstallInfo(var PrevPath, PrevUninst: String): Boolean;
var
  KeyInnoGuid, KeyInnoLegacy, KeyPyLegacy: String;
begin
  Result := False;
  PrevPath := '';
  PrevUninst := '';

  KeyInnoGuid := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{5A8C9B23-7F12-4D39-8C92-E6B3C0F59871}_is1';
  KeyInnoLegacy := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1';
  KeyPyLegacy := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}';

  if QueryUninstallPath(HKLM, KeyInnoGuid, PrevPath, PrevUninst) then
  begin
    Result := True;
    Exit;
  end;
  if QueryUninstallPath(HKCU, KeyInnoGuid, PrevPath, PrevUninst) then
  begin
    Result := True;
    Exit;
  end;
  if IsWin64 then
  begin
    if QueryUninstallPath(HKLM32, KeyInnoGuid, PrevPath, PrevUninst) then
    begin
      Result := True;
      Exit;
    end;
    if QueryUninstallPath(HKCU32, KeyInnoGuid, PrevPath, PrevUninst) then
    begin
      Result := True;
      Exit;
    end;
  end;

  if QueryUninstallPath(HKLM, KeyInnoLegacy, PrevPath, PrevUninst) or
     QueryUninstallPath(HKCU, KeyInnoLegacy, PrevPath, PrevUninst) or
     QueryUninstallPath(HKCU, KeyPyLegacy, PrevPath, PrevUninst) or
     QueryUninstallPath(HKLM, KeyPyLegacy, PrevPath, PrevUninst) then
  begin
    Result := True;
    Exit;
  end;

  if DirExists(ExpandConstant('{autopf}\{#MyAppName}')) and
     (FileExists(ExpandConstant('{autopf}\{#MyAppName}\{#MyAppExeName}')) or
      FileExists(ExpandConstant('{autopf}\{#MyAppName}\unins000.exe'))) then
  begin
    PrevPath := ExpandConstant('{autopf}\{#MyAppName}');
    Result := True;
  end;
end;

procedure CleanupLegacyPythonUninstallKey();
var
  LegacyKey: String;
begin
  LegacyKey := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}';
  if RegKeyExists(HKCU, LegacyKey) then
    RegDeleteKeyIncludingSubkeys(HKCU, LegacyKey);
  if RegKeyExists(HKLM, LegacyKey) then
    RegDeleteKeyIncludingSubkeys(HKLM, LegacyKey);
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

// ===============================================================================
// 설치 진행 순서 제어:
//   1. 기존 앱 실행 중이면 즉시 강제 종료
//   2. 기존 앱 설치 감지 시 사용자에게 삭제 / 덮어쓰기 선택 질의
//   3. 라이선스 선언 (wpLicense)
//   4. 설치 (wpSelectDir -> wpInstalling, 프로그램 추가/제거 정식 등록)
//   5. 바탕화면 바로가기 체크 -> 6. 앱 실행 (wpFinished)
// ===============================================================================
function InitializeSetup(): Boolean;
var
  PrevPath, PrevUninst, UninstExe: String;
  PromptMsg: String;
  UserChoice, ResultCode: Integer;
begin
  Result := True;
  CleanInstallSelected := False;
  FinishedLayoutAdjusted := False;

  // [순서 1] 실행 중인 기존 앱 즉시 강제 종료 ({app} 상수 미사용)
  KillAllPowerProcesses();

  // [순서 2] 기존 앱이 인스톨되어 있으면 사용자에게 삭제/덮어쓰기 질의 후 진행
  if GetExistingInstallInfo(PrevPath, PrevUninst) then
  begin
    if PrevPath <> '' then
      UnlockDirectoryBinaries(PrevPath);

    if not WizardSilent() then
    begin
      if IsKoreanUI() then
      begin
        PromptMsg :=
          '[기존 버전 설치 감지]' + #13#10#13#10 +
          '이 PC에 이미 PowerController가 설치되어 있습니다.' + #13#10 +
          '  설치 경로: ' + PrevPath + #13#10#13#10 +
          '기존 앱을 먼저 삭제한 뒤 새로 설치(클린 설치)하시겠습니까?' + #13#10#13#10 +
          '  • [예 (Yes)]     : 기존 앱 삭제 후 새로 설치 (권장)' + #13#10 +
          '  • [아니오 (No)]  : 기존 파일 위에 덮어쓰기(업그레이드) 설치' + #13#10 +
          '  • [취소 (Cancel)]: 설치 취소';
      end
      else
      begin
        PromptMsg :=
          '[Existing Installation Detected]' + #13#10#13#10 +
          'PowerController is already installed on this computer.' + #13#10 +
          '  Location: ' + PrevPath + #13#10#13#10 +
          'Would you like to uninstall the existing version before installing?' + #13#10#13#10 +
          '  - [Yes]    : Uninstall existing app first, then clean install (Recommended)' + #13#10 +
          '  - [No]     : Overwrite / upgrade over existing installation' + #13#10 +
          '  - [Cancel] : Exit setup';
      end;

      UserChoice := MsgBox(PromptMsg, mbConfirmation, MB_YESNOCANCEL);
      if UserChoice = IDYES then
        CleanInstallSelected := True
      else if UserChoice = IDCANCEL then
      begin
        Result := False;
        Exit;
      end;
    end
    else
    begin
      if (ExpandConstant('{param:clean|0}') = '1') or (ExpandConstant('{param:cleaninstall|0}') = '1') then
        CleanInstallSelected := True;
    end;

    if CleanInstallSelected then
    begin
      UninstExe := '';
      if PrevPath <> '' then
      begin
        if FileExists(AddBackslash(PrevPath) + 'unins000.exe') then
          UninstExe := AddBackslash(PrevPath) + 'unins000.exe'
        else if FileExists(AddBackslash(PrevPath) + 'unins001.exe') then
          UninstExe := AddBackslash(PrevPath) + 'unins001.exe';
      end;

      if UninstExe <> '' then
      begin
        Exec(UninstExe, '/SILENT /VERYSILENT /SUPPRESSMSGBOXES /NORESTART', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        Sleep(800);
      end
      else if PrevUninst <> '' then
      begin
        Exec(ExpandConstant('{cmd}'), '/c ' + PrevUninst + ' --silent', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
        Sleep(800);
      end;

      CleanupLegacyPythonUninstallKey();
      if PrevPath <> '' then
        UnlockDirectoryBinaries(PrevPath);
    end;
  end;
end;

procedure InitializeWizard();
begin
  // [순서 5] 설치 완료 화면(wpFinished)에 배치할 바탕화면 바로가기 체크박스 생성
  DesktopShortcutCheck := TNewCheckBox.Create(WizardForm);
  DesktopShortcutCheck.Parent := WizardForm.FinishedPage;
  DesktopShortcutCheck.Caption := ExpandConstant('{cm:CreateDesktopIcon}');
  DesktopShortcutCheck.Checked := True;
  DesktopShortcutCheck.Visible := False;
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  // GUI 설치 시 바탕화면 바로가기 체크를 설치 완료 직후(wpFinished) 단계에서 제공하기 위해 별도 Tasks 페이지는 건너뜀
  // (무인 설치 /SILENT /TASKS="..." 는 영향 없이 그대로 동작)
  if (not WizardSilent()) and (PageID = wpSelectTasks) then
    Result := True;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  OffsetY: Integer;
begin
  if (CurPageID = wpFinished) and (not WizardSilent()) and (DesktopShortcutCheck <> nil) then
  begin
    DesktopShortcutCheck.Left := WizardForm.RunList.Left;
    DesktopShortcutCheck.Width := WizardForm.RunList.Width;
    DesktopShortcutCheck.Height := ScaleY(20);

    if not FinishedLayoutAdjusted then
    begin
      FinishedLayoutAdjusted := True;
      DesktopShortcutCheck.Top := WizardForm.RunList.Top;
      OffsetY := ScaleY(24);
      if WizardForm.RunList.Visible then
      begin
        WizardForm.RunList.Top := WizardForm.RunList.Top + OffsetY;
        if WizardForm.RunList.Height > OffsetY + ScaleY(20) then
          WizardForm.RunList.Height := WizardForm.RunList.Height - OffsetY;
      end;
    end;
    DesktopShortcutCheck.Visible := True;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  TargetDir, PromptMsg: String;
  DesktopLnk, UserDesktopLnk: String;
  UserChoice: Integer;
begin
  Result := True;
  if CurPageID = wpSelectDir then
  begin
    TargetDir := WizardDirValue;
    // 사용자 지정 폴더에 기존 실행파일이 존재할 경우 덮어쓰기 확인
    if (not CleanInstallSelected) and DirExists(TargetDir) and FileExists(AddBackslash(TargetDir) + '{#MyAppExeName}') then
    begin
      if IsKoreanUI() then
      begin
        PromptMsg :=
          '선택하신 폴더에 이미 PowerController 프로그램 파일이 존재합니다.' + #13#10#13#10 +
          '  대상 경로: ' + TargetDir + #13#10#13#10 +
          '기존 파일을 덮어쓰기(업그레이드)하여 설치를 계속하시겠습니까?';
      end
      else
      begin
        PromptMsg :=
          'PowerController already exists in the selected folder.' + #13#10#13#10 +
          '  Target folder: ' + TargetDir + #13#10#13#10 +
          'Overwrite existing files and continue installation?';
      end;
      UserChoice := MsgBox(PromptMsg, mbConfirmation, MB_OKCANCEL);
      if UserChoice <> IDOK then
      begin
        Result := False;
        Exit;
      end;
    end;
  end
  else if CurPageID = wpFinished then
  begin
    // [순서 5] 완료 버튼 클릭 시 바탕화면 바로가기 체크 상태 최종 반영 후 [순서 6] 앱 실행
    DesktopLnk := ExpandConstant('{autodesktop}\{#MyAppName}.lnk');
    UserDesktopLnk := ExpandConstant('{userdesktop}\{#MyAppName}.lnk');

    if (DesktopShortcutCheck <> nil) and (not DesktopShortcutCheck.Checked) then
    begin
      if FileExists(DesktopLnk) then DeleteFile(DesktopLnk);
      if FileExists(UserDesktopLnk) then DeleteFile(UserDesktopLnk);
    end
    else if (DesktopShortcutCheck <> nil) and DesktopShortcutCheck.Checked then
    begin
      if not FileExists(DesktopLnk) then
      begin
        CreateShellLink(
          DesktopLnk,
          '{#MyAppName}',
          ExpandConstant('{app}\{#MyAppExeName}'),
          '',
          ExpandConstant('{app}'),
          ExpandConstant('{app}\PowerController.ico'),
          0,
          SW_SHOWNORMAL
        );
      end;
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  // 파일 복사(추출) 직전(ssInstall) 단계: 실행 중 프로세스 재확인 종료 및 락 해제
  if CurStep = ssInstall then
  begin
    KillAllPowerProcesses();
    UnlockDirectoryBinaries(ExpandConstant('{app}'));
  end
  // 파일 추출 직후(ssPostInstall): 레거시 Python 언인스톨 키 중복 정리 및 방화벽 규칙 사전 무음 등록
  else if CurStep = ssPostInstall then
  begin
    CleanupLegacyPythonUninstallKey();
    RegisterFirewallRulesSilently();
  end;
end;

function InitializeUninstall(): Boolean;
begin
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
    CleanupLegacyPythonUninstallKey();
    RemoveFirewallRulesSilently();
  end;
end;
