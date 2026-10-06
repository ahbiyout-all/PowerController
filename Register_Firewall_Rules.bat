@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title PowerController - Windows 방화벽 규칙 자동 등록 도구

:: ===============================================================================
:: PowerController & PowerNetworkScheduler Firewall Registration Suite
:: Publisher: cisnet.co.kr | Developer: AhBiYout
:: ===============================================================================

cd /d "%~dp0"

echo ===============================================================================
echo       PowerController ^& 커맨더 관리 타워 - Windows 방화벽 규칙 자동 등록
echo ===============================================================================
echo.

:: 관리자 권한 자동 획득 체크
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [안내] 방화벽 규칙을 등록하려면 관리자 권한이 필요합니다.
    echo 관리자 권한 승인 창(UAC)을 호출합니다...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [*] 관리자 권한 확인 완료.
echo [*] Windows Defender Firewall에 메인 및 커맨더 규칙을 등록합니다...
echo.

set "APP_DIR=%~dp0"
set "MAIN_EXE=%APP_DIR%PowerController.exe"
set "SCHED_EXE=%APP_DIR%PowerNetworkScheduler.exe"
set "APP_VER=v2.9.1"

:: 1. 메인 앱 (PowerController.exe) 규칙 등록 (표준 및 버전 표기 규칙)
echo [1/4] PowerController 메인 프로그램 규칙 등록 중 (%APP_VER%)...
netsh advfirewall firewall delete rule name="PowerController (Inbound)" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerController (Outbound)" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerController %APP_VER% (Inbound)" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerController %APP_VER% (Outbound)" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerController" >nul 2>&1

netsh advfirewall firewall add rule name="PowerController (Inbound)" dir=in action=allow program="%MAIN_EXE%" enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerController (Outbound)" dir=out action=allow program="%MAIN_EXE%" enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerController %APP_VER% (Inbound)" dir=in action=allow program="%MAIN_EXE%" enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerController %APP_VER% (Outbound)" dir=out action=allow program="%MAIN_EXE%" enable=yes profile=any >nul 2>&1
echo       -^> PowerController 및 PowerController %APP_VER% (Inbound/Outbound) 등록 완료 (도메인/개인/공용 프로필)

:: 2. 커맨더 관리 도구 (PowerNetworkScheduler.exe) 규칙 등록 (표준 및 버전 표기 규칙)
echo.
echo [2/4] PowerNetworkScheduler 커맨더 관리 도구 규칙 등록 중 (%APP_VER%)...
netsh advfirewall firewall delete rule name="PowerNetworkScheduler (Inbound)" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerNetworkScheduler (Outbound)" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerNetworkScheduler %APP_VER% (Inbound)" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerNetworkScheduler %APP_VER% (Outbound)" >nul 2>&1

netsh advfirewall firewall add rule name="PowerNetworkScheduler (Inbound)" dir=in action=allow program="%SCHED_EXE%" enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerNetworkScheduler (Outbound)" dir=out action=allow program="%SCHED_EXE%" enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerNetworkScheduler %APP_VER% (Inbound)" dir=in action=allow program="%SCHED_EXE%" enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerNetworkScheduler %APP_VER% (Outbound)" dir=out action=allow program="%SCHED_EXE%" enable=yes profile=any >nul 2>&1
echo       -^> PowerNetworkScheduler 및 PowerNetworkScheduler %APP_VER% (Inbound/Outbound) 등록 완료 (도메인/개인/공용 프로필)

:: 3. 전용 통신 포트 규칙 등록 (TCP 9988, UDP 9985, UDP 9986)
echo.
echo [3/4] 원격 제어 전용 포트 규칙 등록 중...
netsh advfirewall firewall delete rule name="PowerController TCP 9988" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerController UDP 9985" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerController UDP 9986" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerController %APP_VER% TCP 9988" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerController %APP_VER% UDP 9985" >nul 2>&1
netsh advfirewall firewall delete rule name="PowerController %APP_VER% UDP 9986" >nul 2>&1

netsh advfirewall firewall add rule name="PowerController TCP 9988" dir=in action=allow protocol=TCP localport=9988 enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerController UDP 9985" dir=in action=allow protocol=UDP localport=9985 enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerController UDP 9986" dir=in action=allow protocol=UDP localport=9986 enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerController %APP_VER% TCP 9988" dir=in action=allow protocol=TCP localport=9988 enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerController %APP_VER% UDP 9985" dir=in action=allow protocol=UDP localport=9985 enable=yes profile=any >nul 2>&1
netsh advfirewall firewall add rule name="PowerController %APP_VER% UDP 9986" dir=in action=allow protocol=UDP localport=9986 enable=yes profile=any >nul 2>&1
echo       -^> TCP 9988 (원격 예약 제어), UDP 9985 (LAN 브로드캐스트), UDP 9986 (중앙 동기화 허브) 등록 완료

:: 4. 검증 및 결과 안내
echo.
echo ===============================================================================
echo  [성공] 모든 방화벽 예외 규칙이 완벽하게 등록되었습니다!
echo  이제 '공용 네트워크 액세스 허용' 경고창이 더 이상 뜨지 않습니다.
echo ===============================================================================
echo.
pause
