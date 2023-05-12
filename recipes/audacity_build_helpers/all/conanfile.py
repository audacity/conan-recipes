from dataclasses import dataclass
import shutil
from conan import ConanFile, tools
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
    # Used on macOS only to store the initial library name
    lib_line: str = None

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

    def fixup(self, conanfile, executables, lookup_directories):
        package_dir = conanfile.package_folder.lower()

        dependencies = self.__collect_all(conanfile, executables, lookup_directories)

        for dependency in dependencies:
            if dependency.path.lower().startswith(package_dir):
                continue

            target_path = os.path.join(conanfile.package_folder, "bin", dependency.name)

            print(f"Copying {dependency.name} to package folder...")
            shutil.copy(dependency.path, target_path)


class LinuxDependencyProcessor:
    __lookup_directories = []
    __dependencies = {}

    def __init__(self, patchelf_path) -> None:
        if patchelf_path is not None:
            os.environ["PATH"] = patchelf_path + os.pathsep + os.environ["PATH"]

    def __resolve_dependency(self, name):
        for lookup_dir in self.__lookup_directories:
            path = os.path.join(lookup_dir, name)
            if os.path.exists(path):
                return Dependency(name, path)

        return None

    def __run_objdump(self, binary):
        print(f"Running objdump on {binary}")
        try:
            lines = subprocess.check_output(["objdump", "-x", binary]).decode("utf-8").splitlines()
        except subprocess.CalledProcessError:
            print(f"Failed to run objdump on {binary}")
            return []

        for line in lines:
            match = re.match(r"\s+NEEDED\s+(.+\.so.*)", line)
            if match:
                dep = self.__resolve_dependency(match.group(1))
                if dep:
                    yield dep

    def __recursive_collect(self, binary):
        for dependency in self.__run_objdump(binary):
            if dependency.name not in self.__dependencies:
                self.__dependencies[dependency.name] = dependency
                self.__recursive_collect(dependency.path)

    def fixup(self, conanfile, executables, lookup_directories):
        self.__lookup_directories = [os.path.join(conanfile.package_folder, "lib")] + lookup_directories

        for executable in executables:
            self.__recursive_collect(executable)
            subprocess.run(["patchelf", "--set-rpath", "$ORIGIN/../lib", executable])

        for dependency in self.__dependencies.values():
            target_path = os.path.join(conanfile.package_folder, "lib", dependency.name)
            # Do not copy libraries that are already in the package folder
            if not dependency.path.startswith(conanfile.package_folder):
                shutil.copy2(dependency.path, target_path)

            subprocess.check_call(["patchelf", "--set-rpath", "$ORIGIN", target_path])

class MacDependencyProcessor:
    __dependencies = {}
    __lookup_paths = None

    def __is_system_lib(self, path):
        return path.startswith('/System/') or path.startswith('/usr/')

    def __collect_rpaths(self, file):
        result = []

        try:
            with subprocess.Popen(['otool', '-l', file], stdout=subprocess.PIPE) as p:
                lines = [line.decode('utf-8').strip() for line in p.stdout.readlines()]
                for line_index in range(len(lines)):
                    if lines[line_index] == 'cmd LC_RPATH':
                        rpath_match = re.match(r'path\s+(.*)\s+\(', lines[line_index + 2])
                        if rpath_match:
                            rpath = rpath_match.group(1)
                            result.append(rpath)

                    line_index = line_index + 1
        except:
            pass

        return list(set(result))


    def __get_dylib_id(self, file):
        try:
            with subprocess.Popen(['otool', '-D', file], stdout=subprocess.PIPE) as p:
                lines = [line.decode('utf-8').strip() for line in p.stdout.readlines()]
                if len(lines) == 2:
                    return lines[1].split('/')[-1]
        except:
            pass

        return ''


    def __collect_file_dependencies(self, file):
        result = []
        dylib_id = self.__get_dylib_id(file)

        print(f"Collecting dependencies for {file}")
        with subprocess.Popen(['otool', '-L', file], stdout=subprocess.PIPE) as p:
            lines = [line.decode('utf-8').strip() for line in p.stdout.readlines()]
            for line in lines:
                match = re.match(r'(.*)\s+\(', line)
                if match:
                    lib_line = match.group(1)
                    name = lib_line.split('/')[-1]
                    if name != dylib_id and not self.__is_system_lib(lib_line):
                        path = self.__resolve_lib(name)
                        if path is not None:
                            result.append(Dependency(name, path, lib_line))

        return result

    def __resolve_lib(self, lib_name):
        for path in self.__lookup_paths:
            lib_path = os.path.join(path, lib_name)
            if os.path.exists(lib_path):
                return lib_path

        return None

    def __recursive_collect_dependencies(self, name, file):
        dependencies = self.__collect_file_dependencies(file)

        self.__dependencies[name] = {
            'file': file,
            'dependencies': dependencies
        }

        for dependency in dependencies:
            if dependency.name not in self.__dependencies:
                self.__recursive_collect_dependencies(dependency.name, dependency.path)

    def fixup(self, conanfile, executables, lookup_directories):
        self.__lookup_paths = [os.path.join(conanfile.package_folder, "lib")] + lookup_directories

        for file in executables:
            self.__recursive_collect_dependencies(os.path.basename(file), file)

        for name, details in self.__dependencies.items():
            if not details['file'].startswith(conanfile.package_folder):
                # All scanned executables are in the package folder, so we only need to copy the
                # libraries that are not in the package folder
                shutil.copy2(details['file'], os.path.join(conanfile.package_folder, "lib", name))
                details['file'] = os.path.join(conanfile.package_folder, "lib", name)

            install_name_tool_args = []

            rpaths = self.__collect_rpaths(details['file'])
            for rpath in rpaths:
                install_name_tool_args.append("-delete_rpath")
                install_name_tool_args.append(rpath)

            for dependency in details['dependencies']:
                install_name_tool_args.append("-change")
                install_name_tool_args.append(dependency.lib_line)
                if name.endswith(".dylib"):
                    install_name_tool_args.append(f"@loader_path/{dependency.name}")
                else:
                    install_name_tool_args.append(f"@executable_path/../lib/{dependency.name}")

            if len(install_name_tool_args) > 0:
                print(f"Fixing dependencies for {name}")
                subprocess.check_call(["install_name_tool"] + install_name_tool_args + [details['file']])


# Fixes the package that has shared libraries as external dependencies
def fix_external_dependencies(conanfile, executables=None, additional_paths=None, patchelf_path=None):
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
        collector.fixup(conanfile, executables, additional_paths)
    elif conanfile.settings.os == "Macos":
        collector = MacDependencyProcessor()
        collector.fixup(conanfile, executables, additional_paths)
    else:
        collector = LinuxDependencyProcessor(patchelf_path)
        collector.fixup(conanfile, executables, additional_paths)


class AudacityBuildHelpers(ConanFile):
    name = "audacity_build_helpers"
    version = "1.0.0"
    url = "https://github.com/audacity/conan-recipes"
    license = "MIT"
    description = "Build helpers for Audacity"
    exports = "*.py"
    settings = "os"

