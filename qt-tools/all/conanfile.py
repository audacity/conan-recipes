from conan import ConanFile
from conans import tools, CMake

import os
from contextlib import contextmanager

class QtToolsConan(ConanFile):
    name = "qt-tools"
    license = "LGPL-3.0"
    author = "Dmitry Vedenko <dmitry@crsib.me>"
    description = "Qt Tools"
    topics = ("qt", "qt-tools")
    homepage = "https://www.qt.io"
    url = "https://github.com/audacity/conan-recipes"
    settings = "os", "arch", "compiler"

    no_copy_source = True
    short_paths = True

    __cmake = None

    @property
    def _is_msvc(self):
        return str(self.settings.compiler) in ["Visual Studio", "msvc"]

    def source(self):
        tools.get(**self.conan_data["sources"][self.version],
                  strip_root=True, destination="qt6")

    def build_requirements(self):
        self.build_requires("cmake/3.23.2")
        self.build_requires("ninja/1.11.0")
        if self.settings.os == "Windows":
            self.build_requires('strawberryperl/5.30.0.1')

    @contextmanager
    def _build_context(self):
        with tools.vcvars(self) if self._is_msvc else tools.no_op():
            # next lines force cmake package to be in PATH before the one provided by visual studio (vcvars)
            build_env = tools.RunEnvironment(self).vars if self._is_msvc else {}
            build_env["MAKEFLAGS"] = "j%d" % tools.cpu_count()
            if self.settings.os == "Windows":
                if "PATH" not in build_env:
                    build_env["PATH"] = []
                build_env["PATH"].append(os.path.join(self.source_folder, "qt6", "gnuwin32", "bin"))
            if self._is_msvc:
                # this avoids cmake using gcc from strawberryperl
                build_env["CC"] = "cl"
                build_env["CXX"] = "cl"
            with tools.environment_append(build_env):

                if tools.os_info.is_macos:
                    tools.save(".qmake.stash" , "")
                    tools.save(".qmake.super" , "")
                yield

    def __get_cmake(self):
        if self.__cmake:
            return self.__cmake

        cmake = CMake(self, generator="Ninja", build_type="Release")

        cmake.definitions["QT_BUILD_TESTS"] = "OFF"
        cmake.definitions["QT_BUILD_EXAMPLES"] = "OFF"
        cmake.definitions["QT_BUILD_TOOLS"] = "ON"
        cmake.definitions["QT_BUILD_BENCHMARKS"] = "OFF"
        cmake.definitions["QT_BUILD_DOCS"] = "OFF"

        cmake.definitions["QT_BUILD_SUBMODULES"] = "qtbase;qtdeclarative;qtshadertools;qttools"

        cmake.definitions["BUILD_SHARED_LIBS"] = "OFF"
        cmake.definitions["FEATURE_static"] = "ON"
        cmake.definitions["FEATURE_dynamic"] = "OFF"

        if self._is_msvc:
            cmake.definitions["FEATURE_static_runtime"] = "ON"

        cmake.definitions["FEATURE_release"] = "ON"
        cmake.definitions["FEATURE_debug"] = "OFF"
        cmake.definitions["FEATURE_debug_and_release"] = "OFF"
        cmake.definitions["FEATURE_optimize_size"] = "ON"

        cmake.definitions["FEATURE_pkg_config"] = "OFF"
        cmake.definitions["FEATURE_dbus"] = "OFF"
        cmake.definitions["FEATURE_sql"] = "OFF"

        cmake.definitions["BUILD_qtactiveqt"] = "ON"
        cmake.definitions["BUILD_qtbase"] = "ON"
        cmake.definitions["BUILD_qtdeclarative"] = "ON"
        cmake.definitions["BUILD_qtimageformats"] = "ON"
        cmake.definitions["BUILD_qtlanguageserver"] = "ON"
        cmake.definitions["BUILD_qtshadertools"] = "ON"
        cmake.definitions["BUILD_qttools"] = "ON"
        cmake.definitions["BUILD_qtsvg"] = "ON"

        if self.settings.os == "Windows":
            cmake.definitions["HOST_PERL"] = getattr(self, "user_info_build", self.deps_user_info)["strawberryperl"].perl

        self.__cmake = cmake
        return self.__cmake


    def build(self):
        with self._build_context():
            cmake = self.__get_cmake()
            cmake.configure(source_folder="qt6")
            cmake.build()

    def package(self):
        with self._build_context():
            cmake = self.__get_cmake()
            cmake.install()

        self.copy("*LICENSE*", src="qt6/", dst="licenses")
        for dir in os.listdir(self.package_folder):
            if dir == "lib":
                for libdir in os.listdir(os.path.join(self.package_folder, dir)):
                    if not libdir == "cmake":
                        entry_path = os.path.join(self.package_folder, dir, libdir)
                        if os.path.isdir(entry_path):
                            tools.rmdir(os.path.join(self.package_folder, dir, libdir))
                        else:
                            os.remove(entry_path)
            elif dir not in ["bin", "qml", "libexec"]:
                tools.rmdir(os.path.join(self.package_folder, dir))

        tools.remove_files_by_mask(self.package_folder, "*.pdb*")
        tools.remove_files_by_mask(self.package_folder, "*.lib*")
        tools.remove_files_by_mask(self.package_folder, "*.exp*")
        tools.remove_files_by_mask(self.package_folder, "*.a*")
        tools.remove_files_by_mask(self.package_folder, "*.la*")
        tools.remove_files_by_mask(self.package_folder, "*.prl*")
        tools.remove_files_by_mask(self.package_folder, "*.pc*")
        tools.remove_files_by_mask(self.package_folder, "*.cmake*")
        tools.remove_files_by_mask(self.package_folder, "*.o*")

        with open(os.path.join(self.package_folder, "bin", "qt.conf"), "w") as f:
            f.write("[Paths]\nPrefix = ..")

    def package_info(self):
        self.env_info.PATH.append(os.path.join(self.package_folder, "bin"))
        self.user_info.rootpath = self.package_folder

