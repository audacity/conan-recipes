from conan import ConanFile, tools
from conan.tools.cmake import cmake_layout
from conan.tools.env import Environment
from contextlib import contextmanager
import os


class TestPackageConan(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    generators = "VCVars", "VirtualRunEnv", "VirtualBuildEnv"

    def build_requirements(self):
        self.build_requires("ninja/1.11.0@audacity/stable")
        self.build_requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    @contextmanager
    def _build_context(self):
        if self.settings.compiler == "msvc":
            yield
        else:
            compiler_defaults = Environment()

            if self.settings.compiler == "gcc":
                compiler_defaults.define("CC", "gcc")
                compiler_defaults.define("CXX", "g++")
                compiler_defaults.define("AR", "ar")
                compiler_defaults.define("LD", "g++")
            elif self.settings.compiler == "clang":
                compiler_defaults.define("CC", "clang")
                compiler_defaults.define("CXX", "clang++")
                compiler_defaults.define("AR", "ar")
                compiler_defaults.define("LD", "clang++")

            with compiler_defaults.vars(self).apply():
                yield

    @property
    def _target_os(self):
        if tools.apple.is_apple_os(self):
            return "mac"
        # Assume gn knows about the os
        return {
            "Windows": "win",
        }.get(str(self.settings.os), str(self.settings.os).lower())

    @property
    def _target_cpu(self):
        return {
            "x86_64": "x64",
        }.get(str(self.settings.arch), str(self.settings.arch))

    def build(self):
        if not tools.build.cross_building(self):
            with tools.files.chdir(self, self.source_folder):
                gn_args = [
                    os.path.relpath(os.path.join(self.build_folder, "bin"), os.getcwd()).replace("\\", "/"),
                    "--args=\"target_os=\\\"{os_}\\\" target_cpu=\\\"{cpu}\\\"\"".format(os_=self._target_os, cpu=self._target_cpu),
                ]
                self.run("gn gen {}".format(" ".join(gn_args)))
            with self._build_context():
                self.run("ninja -v -j{} -C bin".format(tools.build.build_jobs(self)))

    def test(self):
        if not tools.build.cross_building(self):
            self.run(os.path.join("bin", "test_package"))
