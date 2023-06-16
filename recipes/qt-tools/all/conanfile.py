from conan import ConanFile

from conan.tools.cmake import CMake, cmake_layout, CMakeToolchain
from conan.tools.files import get, copy

import os

class QtToolsConan(ConanFile):
    name = "qt-tools"
    license = "LGPL-3.0"
    author = "Dmitry Vedenko <dmitry@crsib.me>"
    description = "Qt Tools"
    topics = ("qt", "qt-tools")
    homepage = "https://www.qt.io"
    url = "https://github.com/audacity/conan-recipes"
    settings = "os", "arch", "compiler", "build_type"
    package_type = "application"

    no_copy_source = True

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
                  strip_root=True)

    def build_requirements(self):
        self.build_requires("cmake/[>=3.22.0]@audacity/stable")
        self.build_requires("ninja/[>=1.11.0]@audacity/stable")
        if self.settings.os == "Windows":
            self.build_requires('strawberryperl/[>=5.30.0.1]@audacity/stable')

    def layout(self):
        cmake_layout(self, src_folder='src')

    def generate(self):

        tc = CMakeToolchain(self, generator="Ninja")

        tc.variables["QT_BUILD_TOOLS"] = "ON"
        tc.variables["QT_BUILD_DOCS"] = "ON"
        tc.variables["QT_BUILD_TESTS"] = "OFF"
        tc.variables["QT_BUILD_EXAMPLES"] = "OFF"
        tc.variables["QT_BUILD_BENCHMARKS"] = "OFF"

        tc.variables["FEATURE_static"] = "OFF"
        tc.variables["FEATURE_dynamic"] = "ON"
        tc.variables["BUILD_SHARED_LIBS"] = "ON"

        tc.variables["FEATURE_release"] = "ON"
        tc.variables["FEATURE_debug"] = "OFF"
        tc.variables["FEATURE_debug_and_release"] = "OFF"
        tc.variables["FEATURE_optimize_size"] = "ON"
        tc.variables["FEATURE_sql"] = "ON"
        tc.variables["FEATURE_sql_sqlite"] = "ON"
        tc.variables["FEATURE_help"] = "ON"
        tc.variables["FEATURE_printsupport"] = "ON"

        if self.settings.os == "Windows":
            tc.variables["HOST_PERL"] = self.dependencies.build["strawberryperl"].conf_info.get("user.strawberryperl:perl", check_type=str)

        tc.generate()


    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        copy(self, "*LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        with open(os.path.join(self.package_folder, "bin", "qt.conf"), "w") as f:
            f.write("[Paths]\nPrefix = ..")

    def package_info(self):
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.conf_info.define("user.qt_tools:rootpath", self.package_folder)

    def package_id(self):
        del self.info.settings.compiler
        del self.info.settings.build_type
