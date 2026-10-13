@echo off
setlocal
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install.ps1" %*
if errorlevel 1 (
  echo.
  echo Installation failed. See the message above and data\installation.log.
  pause
  exit /b 1
)
