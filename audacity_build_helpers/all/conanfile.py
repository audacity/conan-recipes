from dataclasses import dataclass
import shutil
from conans import ConanFile, tools
import os
import re
import subprocess


# This functions returns a list of all executables in the package folder
# It can potentially give false postives, treating scripts as executables
def collect_executables(conanfile):
    tools = []

    lookup_dirs = [
        os.path.join(conanfile.package_folder, "bin"),
        os.path.join(conanfile.package_folder, "libexec")
    ]

    skip_extensions = [
        ".dylib",
        ".so",
        ".sh",
        ".bat",
        ".ps1",
        ".py",
        ".pl",
    ]

    for lookup_dir in lookup_dirs:
        if not os.path.exists(lookup_dir):
            continue
        for root, _, files in os.walk(lookup_dir):
            for filename in files:
                if filename.endswith(".exe") or os.access(os.path.join(root, filename), os.X_OK):
                    if not any(filename.endswith(ext) for ext in skip_extensions):
                        tools.append(os.path.join(root, filename))

    return tools

@dataclass
class Dependency:
    name: str
    path: str

class WindowsDependencyProcessor:
    __dependencies = {}

    def __run_dumpbin(self, binary, looukp_directories):
        try:
            output = subprocess.check_output(["dumpbin.exe", '/dependents', binary]).decode('utf-8')

            if output is None:
                return []

            dependencies = []

            print(f"Collecting dependencies for {binary}...")

            for line in output.splitlines():
                if re.match(r'^\s+.*\.dll$', line, re.IGNORECASE):
                    dependency_name = line.strip()
                    for lookup_dir in looukp_directories:
                        dependency_path = os.path.join(lookup_dir, dependency_name)
                        if os.path.exists(dependency_path):
                            dependencies.append(Dependency(dependency_name, dependency_path))
                            break

            return dependencies

        except subprocess.CalledProcessError:
            print("Failed to run dumpbin.exe on " + binary)
            return []

    def __recursive_collect(self, binary, lookup_directories):
        dependencies = self.__run_dumpbin(binary, [os.path.dirname(binary)] + lookup_directories)

        for dependency in dependencies:
            if dependency.name not in self.__dependencies:
                self.__dependencies[dependency.name] = dependency
                self.__recursive_collect(dependency.path, lookup_directories)

    def __collect_all(self, conanfile, executables, looukp_directories):
        with tools.vcvars(conanfile):
            for executable in executables:
                self.__recursive_collect(executable, looukp_directories)

        return self.__dependencies.values()

    def fixup(self, conanfile, executables, looukp_directories):
        package_dir = conanfile.package_folder.lower()

        dependencies = self.__collect_all(conanfile, executables, looukp_directories)

        for dependency in dependencies:
            if dependency.path.lower().startswith(package_dir):
                continue

            target_path = os.path.join(conanfile.package_folder, "bin", dependency.name)

            if os.path.exists(target_path):
                continue

            print(f"Copying {dependency.name} to package folder...")
            shutil.copy(dependency.path, target_path)



# Fixes the package that has shared libraries as external dependencies
def fix_external_dependencies(conanfile, executables=None, additional_paths=None):
    print("Collecting dependencies...")
    if not executables:
        executables = collect_executables(conanfile)

    if not additional_paths:
        additional_paths = []

    for dep in conanfile.dependencies.host.values():
        if len(dep.cpp_info.libdirs) > 0:
            additional_paths.append(dep.cpp_info.libdirs[0])
        if conanfile.settings.os == "Windows" and len(dep.cpp_info.bindirs) > 0:
            additional_paths.append(dep.cpp_info.bindirs[0])

    if conanfile.settings.os == "Windows":
        collector = WindowsDependencyProcessor()
        return collector.fixup(conanfile, executables, additional_paths)


class AudacityBuildHelpers(ConanFile):
    name = "audacity_build_helpers"
    version = "1.0.0"
    url = "https://github.com/audacity/conan-recipes"
    license = "MIT"
    description = "Build helpers for Audacity"
    exports = "*.py"
