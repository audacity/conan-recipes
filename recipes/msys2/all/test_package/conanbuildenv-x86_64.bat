@echo off
chcp 65001 > nul
setlocal
echo @echo off > "%~dp0/deactivate_conanbuildenv-x86_64.bat"
echo echo Restoring environment >> "%~dp0/deactivate_conanbuildenv-x86_64.bat"
for %%v in (MSYS_ROOT MSYS_BIN PATH) do (
    set foundenvvar=
    for /f "delims== tokens=1,2" %%a in ('set') do (
        if /I "%%a" == "%%v" (
            echo set "%%a=%%b">> "%~dp0/deactivate_conanbuildenv-x86_64.bat"
            set foundenvvar=1
        )
    )
    if not defined foundenvvar (
        echo set %%v=>> "%~dp0/deactivate_conanbuildenv-x86_64.bat"
    )
)
endlocal


set "MSYS_ROOT=C:\devel\projects\github\conan-io\conan-recipes\utils\.conan_utils\conan\p\msys2f38c9328a4443\p\bin\msys64"
set "MSYS_BIN=C:\devel\projects\github\conan-io\conan-recipes\utils\.conan_utils\conan\p\msys2f38c9328a4443\p\bin\msys64\usr\bin"
set "PATH=C:\devel\projects\github\conan-io\conan-recipes\utils\.conan_utils\conan\p\msys2f38c9328a4443\p\bin;C:\devel\projects\github\conan-io\conan-recipes\utils\.conan_utils\conan\p\msys2f38c9328a4443\p\bin\msys64\usr\bin;%PATH%"