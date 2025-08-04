@echo off
echo Welcome to the uRPC release script!
echo The script will create a release archive for uRPC.
echo.

echo Checking dependencies...
echo Check git...
where /q git
if not %errorlevel% == 0 (
    echo ERROR: git is not found! Check the installation and/or PATH.
    goto FAIL
) else (
    echo ***** Done!
)

echo Check 7z...
where /q 7z
if not %errorlevel% == 0 (
    echo ERROR: 7z is not found! Check the installation and/or PATH.
    goto FAIL
) else (
    echo ***** Done!
)

echo Find version information...
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
echo Found version: %MAJOR%.%MINOR%.%PATCH%

REM Clean up the repository and create an archive...
echo Cleaning up the repository...
git clean -xdf
echo Updating submodules...
git submodule update --init --recursive

echo Creating archive...
set "ARCHIVE_NAME=urpc-%MAJOR%.%MINOR%.%PATCH%.zip"
7z a -tzip -r -x!".git*" -x!"release.bat" "%ARCHIVE_NAME%" *

echo Archive created: %ARCHIVE_NAME%
