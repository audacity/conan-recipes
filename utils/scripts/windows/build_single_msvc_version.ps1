$ErrorActionPreference = "Stop"
$PSDefaultParameterValues['*:ErrorAction']='Stop'
function ThrowOnNativeFailure {
    if (-not $?)
    {
        throw 'Native Failure'
    }
}

Function Fast-Delete {
    Param(
        [Parameter(Valuefrompipeline=$True, Mandatory=$True)] [String]$Directory
    )

    $emptyDir = GetRandomTempPath
    mkdir $emptyDir

    Write-Warning "Deleting $Directory"
    Write-Output "Temporary directory: $emptyDir"

    robocopy $emptyDir $Directory /mir | Out-Null
    #ThrowOnNativeFailure

    Remove-Item -Path $Directory -erroraction silentlycontinue
    Remove-Item -Path $emptyDir -erroraction silentlycontinue

    Write-Warning "Deleted $Directory with status $LastExitCode"
}

Function GetRandomTempPath {
    Do {
        $fullPath = Join-Path -Path $env:TEMP -ChildPath ([System.IO.Path]::GetRandomFileName())
    } While (Test-Path $fullPath);

    Return $fullPath;
}

$msvc_version="2022"
$build_dir="C:\t"

$audacity3_repo="https://github.com/audacity/audacity.git"
$audacity3_branch="master"
$audacity3_build_order="build_order.yml"
$audacity3_build_config="audacity3"

$audacity4_repo="https://github.com/audacity/audacity.git"
$audacity4_branch="qt"
$audacity4_build_order="build_order_qt.yml"
$audacity4_build_config="audacity4"

$script_location = split-path -parent $MyInvocation.MyCommand.Definition

$conan_utils="${script_location}\..\..\conan-utils.py"

pip3 install -r $script_location\..\..\requirements.txt

if (Test-Path "$script_location\$msvc_version") {
    Fast-Delete "$script_location\$msvc_version"
}

if (Test-Path "$build_dir") {
    Fast-Delete "$build_dir"
}

mkdir "$script_location\$msvc_version"
Set-Location "$script_location\$msvc_version"

python ${conan_utils} --output-dir "$build_dir" --short-paths  init-env --clean
ThrowOnNativeFailure
python ${conan_utils} --output-dir "$build_dir" --short-paths  add-remote --name conan-utils-audacity-binaries-conan2 --url https://artifactory.audacityteam.org/artifactory/api/conan/audacity-binaries-conan2
ThrowOnNativeFailure

# Audacity 3

#if (Test-Path "audacity") {
#    Fast-Delete "audacity"
#}
#
#git clone --depth 1 ${audacity3_repo} --branch ${audacity3_branch}
#
#python ${conan_utils} --output-dir "$build_dir" --short-paths  validate-recipe `
#        --remote conan-utils-audacity-binaries-conan2 --profile-host "host/windows/msvc${msvc_version}_x86_64_rel" --profile-build "build/windows/msvc${msvc_version}_x86_64" `
#        --build-order ${audacity3_build_order} --recipe-config ${audacity3_build_config} --recipe audacity/conan/conanfile.py --enable-debug-processor sentry --enable-debug-processor symstore
#ThrowOnNativeFailure
#
#python ${conan_utils} --output-dir "$build_dir" --short-paths validate-recipe `
#        --remote conan-utils-audacity-binaries-conan2 --profile-host "host/windows/msvc${msvc_version}_x86_64_deb" --profile-build "build/windows/msvc${msvc_version}_x86_64" `
#        --build-order ${audacity3_build_order} --recipe-config ${audacity3_build_config} --recipe audacity/conan/conanfile.py
#ThrowOnNativeFailure

#python ${conan_utils} --output-dir "$build_dir" --short-paths validate-recipe `
#        --remote conan-utils-audacity-binaries-conan2 --profile-host "host/windows/msvc${msvc_version}_x86_rel" --profile-build "build/windows/msvc${msvc_version}_x86_64" `
#        --build-order ${audacity3_build_order} --recipe-config ${audacity3_build_config} --recipe audacity/conan/conanfile.py --enable-debug-processor sentry --enable-debug-processor symstore
#ThrowOnNativeFailure
#
#python ${conan_utils} --output-dir "$build_dir" --short-paths validate-recipe `
#        --remote conan-utils-audacity-binaries-conan2 --profile-host "host/windows/msvc${msvc_version}_x86_deb" --profile-build "build/windows/msvc${msvc_version}_x86_64" `
#        --build-order ${audacity3_build_order} --recipe-config ${audacity3_build_config} --recipe audacity/conan/conanfile.py
#ThrowOnNativeFailure
#
# Audacity 4

if (Test-Path "audacity") {
    Fast-Delete "audacity"
}

git clone --depth 1 ${audacity4_repo} --branch ${audacity4_branch}

python ${conan_utils} --output-dir "$build_dir" --short-paths validate-recipe `
        --remote conan-utils-audacity-binaries-conan2 --profile-host "host/windows/msvc${msvc_version}_x86_64_rel" --profile-build "build/windows/msvc${msvc_version}_x86_64" `
        --build-order ${audacity4_build_order} --recipe-config ${audacity4_build_config} --recipe audacity/conan/conanfile.py --enable-debug-processor sentry --enable-debug-processor symstore
ThrowOnNativeFailure

python ${conan_utils} --output-dir "$build_dir" --short-paths validate-recipe `
        --remote conan-utils-audacity-binaries-conan2 --profile-host "host/windows/msvc${msvc_version}_x86_64_deb" --profile-build "build/windows/msvc${msvc_version}_x86_64" `
        --build-order ${audacity4_build_order} --recipe-config ${audacity4_build_config} --recipe audacity/conan/conanfile.py
ThrowOnNativeFailure

# Do not build 32-bit Qt version for now

#python ${conan_utils} --output-dir "$build_dir" --short-paths validate-recipe `
#        --remote conan-utils-audacity-binaries-conan2 --profile-host "host/windows/msvc${msvc_version}_x86_rel" --profile-build "build/windows/msvc${msvc_version}_x86_64" `
#        --build-order ${audacity4_build_order} --recipe-config ${audacity4_build_config} --recipe audacity/conan/conanfile.py --enable-debug-processor sentry --enable-debug-processor symstore
#ThrowOnNativeFailure
#
#python ${conan_utils} --output-dir "$build_dir" --short-paths validate-recipe `
#        --remote conan-utils-audacity-binaries-conan2 --profile-host "host/windows/msvc${msvc_version}_x86_deb" --profile-build "build/windows/msvc${msvc_version}_x86_64" `
#        --build-order ${audacity4_build_order} --recipe-config ${audacity4_build_config} --recipe audacity/conan/conanfile.py
#ThrowOnNativeFailure
#

# Upload artifacts

if ($msvc_version -eq "2022") {
    python ${conan_utils} --output-dir "$build_dir" --short-paths upload --build-order ${audacity3_build_order} --upload-build-tools
    ThrowOnNativeFailure
    python ${conan_utils} --output-dir "$build_dir" --short-paths upload --build-order ${audacity4_build_order} --upload-build-tools
    ThrowOnNativeFailure
} else{
    python ${conan_utils} --output-dir "$build_dir" --short-paths upload --build-order ${audacity3_build_order}
    ThrowOnNativeFailure
    python ${conan_utils} --output-dir "$build_dir" --short-paths upload --build-order ${audacity4_build_order}
    ThrowOnNativeFailure
}

Fast-Delete "$build_dir"
