@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0zip_extract_helper.ps1" %*
