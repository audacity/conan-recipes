@echo off
chcp 65001 > nul
setlocal
echo @echo off > "%~dp0/deactivate_conanbuildenv_pkg_config_path.bat"
echo echo Restoring environment >> "%~dp0/deactivate_conanbuildenv_pkg_config_path.bat"
for %%v in (PKG_CONFIG_PATH) do (
    set foundenvvar=
    for /f "delims== tokens=1,2" %%a in ('set') do (
        if /I "%%a" == "%%v" (
            echo set "%%a=%%b">> "%~dp0/deactivate_conanbuildenv_pkg_config_path.bat"
            set foundenvvar=1
        )
    )
    if not defined foundenvvar (
        echo set %%v=>> "%~dp0/deactivate_conanbuildenv_pkg_config_path.bat"
    )
)
endlocal


set "PKG_CONFIG_PATH=SECRET_CONAN_PKG_VARIABLE"