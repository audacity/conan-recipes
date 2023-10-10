#
# This file is part of KDDockWidgets.
#
# SPDX-FileCopyrightText: 2020-2023 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only
#
# Contact KDAB at <info@kdab.com> for commercial licensing options.
#

from conan import ConanFile
from conan.tools.files import get
from conan.tools.build import cross_building
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.scm import Version

class KDDockWidgetsConan(ConanFile):
    name = "kddockwidgets"
    default_user = "audacity"
    default_channel = "testing"
    license = ("https://raw.githubusercontent.com/KDAB/KDDockWidgets/master/LICENSES/GPL-2.0-only.txt",
               "https://raw.githubusercontent.com/KDAB/KDDockWidgets/master/LICENSES/GPL-3.0-only.txt")
    author = "Klaralvdalens Datakonsult AB (KDAB) info@kdab.com"
    url = "https://github.com/KDAB/KDDockWidgets"
    description = "Advanced Dock Widget Framework for Qt"
    topics = ("qt", "dockwidget", "kdab")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "qt_version": ["ANY"],
        "shared": [True, False],
        "build_examples": [True, False],
        "build_tests": [True, False],
        "build_python_bindings": [True, False],
        "build_for_qt6": [True, False],
    }

    default_options = {
        "qt_version": "qt/6.3.1@audacity/stable",
        "shared": False,
        "build_examples": False,
        "build_tests": False,
        "build_python_bindings": False,
        "build_for_qt6": True,
    }

    @property
    def __use_system_qt(self):
        return str(self.options.qt_version) == 'system'

    def requirements(self):
        if not self.__use_system_qt:
            # Check https://docs.conan.io/en/latest/reference/conanfile/attributes.html#version-ranges for more info about versioning
            self.requires(str(self.options.qt_version))

    def build_requirements(self):
        self.tool_requires("ninja/1.11.0@audacity/stable")

        if cross_building(self, skip_x64_x86=True):
            self.tool_requires("qt-tools/6.3.1@audacity/stable", package_id_mode="minor_mode")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def configure(self):
        if self.options.shared:
            self.options["*"].shared = True
        if not self.__use_system_qt:
            self.options["qt"].qtdeclarative = True
            self.options["qt"].qtshadertools = True

    def generate(self):
        CMakeDeps(self).generate()

        tc = CMakeToolchain(self, generator="Ninja")
        tc.variables["KDDockWidgets_STATIC"] = not self.options.shared
        tc.variables["KDDockWidgets_EXAMPLES"] = self.options.build_examples
        tc.variables["KDDockWidgets_TESTS"] = self.options.build_tests
        tc.variables["KDDockWidgets_PYTHON_BINDINGS"] = self.options.build_python_bindings
        tc.variables["KDDockWidgets_QT6"] = self.options.build_for_qt6

        if Version(self.version).major < "2":
            tc.variables["KDDockWidgets_QTQUICK"] = True
        else:
            tc.variables["KDDockWidgets_FRONTENDS"] = 'qtwidgets;qtquick'

        if not self.__use_system_qt and cross_building(self, skip_x64_x86=True):
            host_tools = self.dependencies.direct_build["qt-tools"].package_folder
            tc.variables["QT_HOST_PATH"] = host_tools
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)

        self.cpp_info.set_property("cmake_find_mode", "config")
        self.cpp_info.set_property("cmake_target_name", "KDAB::kddockwidgets")

        if self.options.build_for_qt6:
            self.cpp_info.includedirs = [ "include/kddockwidgets-qt6" ]
            self.cpp_info.set_property("cmake_file_name", "KDDockWidgets-qt6")
        else:
            self.cpp_info.set_property("cmake_file_name", "KDDockWidgets")
