import os
import shutil

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.files import copy

class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeToolchain", "CMakeDeps", "VirtualRunEnv"

    def build_requirements(self):
        self.build_requires("cmake/[>=3.22.0]@audacity/stable")
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            bin_dir = self.cpp.build.bindirs[0]
            self.run(os.path.join(bin_dir, "test_package"), env="conanrun")
