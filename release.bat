@echo off

REM Find version numbers in version.py
set "VERSION_FILE=version.py"
set "MAJOR="
set "MINOR="
set "PATCH="

for /f "tokens=1,2 delims== " %%a in ('findstr /r /c:"^BUILDER_VERSION_MAJOR\ =\ [0-9][0-9]*" "%VERSION_FILE%"') do (
    set "MAJOR=%%b"
)
for /f "tokens=1,2 delims== " %%a in ('findstr /r /c:"^BUILDER_VERSION_MINOR\ =\ [0-9][0-9]*" "%VERSION_FILE%"') do (
    set "MINOR=%%b"
)
for /f "tokens=1,2 delims== " %%a in ('findstr /r /c:"^BUILDER_VERSION_BUGFIX\ =\ [0-9][0-9]*" "%VERSION_FILE%"') do (
    set "PATCH=%%b"
)

if "%MAJOR%"=="" (
    echo Major version not found in %VERSION_FILE%
    exit /b 1
)
if "%MINOR%"=="" (
    echo Minor version not found in %VERSION_FILE%
    exit /b 1
)
if "%PATCH%"=="" (
    echo Patch version not found in %VERSION_FILE%
    exit /b 1
)


set "ARCHIVE_NAME=urpc-%MAJOR%.%MINOR%.%PATCH%.zip"
7z a -tzip -r -x!".git*" -x!"release.bat" "%ARCHIVE_NAME%" *

echo Archive created: %ARCHIVE_NAME%
