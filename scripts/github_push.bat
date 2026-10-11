@echo off
setlocal enabledelayedexpansion
title GitHub Auto Push and Release Pipeline - PowerController
color 0b

:: Change to project root directory
cd /d "%~dp0\.."

echo ================================================================
echo   PowerController - GitHub Automated Push ^& Release Pipeline
echo   Developer : AhBiYout (GitHub: AhBiYout-all)
echo   Target    : https://github.com/AhBiYout-all/PowerController.git
echo   Official  : https://ahbiyoutvibe.blogspot.com/
echo   Company   : https://www.cisnet.co.kr
echo ================================================================
echo(

:: Call root push_to_github.bat
call "%~dp0\..\push_to_github.bat"
