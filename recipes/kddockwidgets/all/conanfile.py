#
# This file is part of KDDockWidgets.
#
# SPDX-FileCopyrightText: 2020-2023 Klarälvdalens Datakonsult AB, a KDAB Group company <info@kdab.com>
# SPDX-License-Identifier: GPL-2.0-only OR GPL-3.0-only
#
# Contact KDAB at <info@kdab.com> for commercial licensing options.
#

from conans import ConanFile, tools
from conan.tools.cmake import cmake_layout, CMakeDeps, CMake, CMakeToolchain
from conan.tools.build import cross_building

class KDDockWidgetsConan(ConanFile):
    name = "kddockwidgets"
    version = "1.6.0"
    default_user = "audacity"
    default_channel = "testing"
    license = ("https://raw.githubusercontent.com/KDAB/KDDockWidgets/master/LICENSES/GPL-2.0-only.txt",
               "https://raw.githubusercontent.com/KDAB/KDDockWidgets/master/LICENSES/GPL-3.0-only.txt")
    author = "Klaralvdalens Datakonsult AB (KDAB) info@kdab.com"
    url = "https://github.com/KDAB/KDDockWidgets"
    description = "Advanced Dock Widget Framework for Qt"
    generators = "CMakeDeps"
    topics = ("qt", "dockwidget", "kdab")
    settings = "os", "compiler", "build_type", "arch"
    options = {
        "qt_version": "ANY",
        "shared": [True, False],
        "build_examples": [True, False],
        "build_tests": [True, False],
        "build_python_bindings": [True, False],
        "build_for_qt6": [True, False],
    }

    default_options = {
        "qt_version": "qt/6.3.1@audacity/testing",
        "shared": False,
        "build_examples": False,
        "build_tests": False,
        "build_python_bindings": False,
        "build_for_qt6": True,
    }

    def requirements(self):
        # Check https://docs.conan.io/en/latest/reference/conanfile/attributes.html#version-ranges for more info about versioning
        self.requires(str(self.options.qt_version))

    def build_requirements(self):
        self.tool_requires("ninja/1.11.0")

        if cross_building(self, skip_x64_x86=True):
            self.tool_requires("qt-tools/6.3.1@audacity/testing")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        tools.rename(extracted_dir, "source_subfolder")

    def configure(self):
        if self.options.shared:
            self.options["*"].shared = True

        self.options["qt"].qtdeclarative = True
        # Required to enable Quick
        self.options["qt"].qtshadertools = True

    def generate(self):
        tc = CMakeToolchain(self, generator="Ninja")
        tc.cache_variables["KDDockWidgets_STATIC"] = not self.options.shared
        tc.cache_variables["KDDockWidgets_EXAMPLES"] = self.options.build_examples
        tc.cache_variables["KDDockWidgets_TESTS"] = self.options.build_tests
        tc.cache_variables["KDDockWidgets_PYTHON_BINDINGS"] = self.options.build_python_bindings
        tc.cache_variables["KDDockWidgets_QT6"] = self.options.build_for_qt6
        tc.cache_variables["KDDockWidgets_QTQUICK"] = True
        if cross_building(self, skip_x64_x86=True):
            host_tools = self.dependencies.direct_build["qt-tools"].package_folder
            tc.cache_variables["QT_HOST_PATH"] = host_tools
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def layout(self):
        cmake_layout(self)

    def build(self):
        self.cmake = CMake(self)
        self.cmake.configure(build_script_folder="source_subfolder")
        self.cmake.build()

    def package(self):
        self.cmake.install()

    def package_info(self):
        self.env_info.CMAKE_PREFIX_PATH.append(self.package_folder)
        self.cpp_info.includedirs = [ "include/kddockwidgets-qt6" ]

    def package_id(self):
        # Check only the major and minor version!
        self.info.requires["qt"].minor_mode()
