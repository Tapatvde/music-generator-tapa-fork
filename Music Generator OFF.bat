@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\fork-control.ps1" -Action Stop
