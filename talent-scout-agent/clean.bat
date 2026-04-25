@echo off
REM ============================================================
REM  Talent Scout — Cleanup Script
REM  Removes auto-generated files (caches, builds, logs)
REM  Safe to run anytime. Does NOT touch venv, node_modules, .env
REM ============================================================

echo.
echo === Cleaning Talent Scout project ===
echo.

REM Python bytecode caches
echo [1/4] Removing Python __pycache__ folders...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Python compiled files
echo [2/4] Removing .pyc files...
del /s /q *.pyc 2>nul

REM Frontend build output
echo [3/4] Removing frontend build artifacts...
if exist "frontend\dist" rmdir /s /q "frontend\dist"

REM OS junk
echo [4/4] Removing OS clutter...
del /s /q .DS_Store 2>nul
del /s /q Thumbs.db 2>nul

echo.
echo === Cleanup complete ===
echo.
pause