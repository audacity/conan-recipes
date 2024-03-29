from io import StringIO
import os
from pathlib import Path
import re

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import cmake_layout, CMake, CMakeDeps, CMakeToolchain
from conan.tools.env import Environment, VirtualBuildEnv
from conan.tools.gnu import Autotools, AutotoolsToolchain
from conan.tools.microsoft import unix_path
from conan.tools.files import rm, rmdir


# It will become the standard on Conan 2.x
class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    test_type = "explicit"
    win_bash = True

    @property
    def _settings_build(self):
        return getattr(self, "settings_build", self.settings)

    def requirements(self):
        self.requires(self.tested_reference_str) # for the library

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str) # for the executable
        self.tool_requires("automake/1.16.5@audacity/stable")
        if self._settings_build.os == "Windows" and not self.conf.get("tools.microsoft.bash:path", check_type=str):
            self.tool_requires("msys2/cci.latest@audacity/stable")

    def layout(self):
        cmake_layout(self, src_folder="sources")

    def generate(self):
        # Autotools project to test integration pkgconfig works
        # during an Autotools configure run
        at = AutotoolsToolchain(self)
        at.generate()

        # Expose `PKG_CONFIG_PATH` to be able to find libexample1.pc
        env = Environment()
        self.output.warning(f"Source folder: {self.source_folder}")
        env.prepend_path("PKG_CONFIG_PATH", self.source_folder)
        env.vars(self, scope="build").save_script("pkgconf-config-path")

        buildenv = VirtualBuildEnv(self)
        buildenv.generate()

        # CMake project to test that we can link against the library,
        # when the library is built
        if self.dependencies[self.tested_reference_str].options.enable_lib:
            ct = CMakeToolchain(self)
            ct.generate()
            deps = CMakeDeps(self)
            deps.generate()

    @property
    def _testing_library(self):
        # Workaround, in Conan >=2.0 we should be able to remove this in favour of:
        # self.dependencies[self.tested_reference_str].options.enable_lib
        has_toolchain = sorted(Path(self.build_folder).rglob('conan_toolchain.cmake'))
        return has_toolchain

    def build(self):
        # Test that configure doesn't fail, we are not building the
        # autotools project
        autotools = Autotools(self)
        autotools.autoreconf()
        autotools.configure()

        if self._testing_library:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()

    def test(self):
        # Check that we can find pkgconf in build environment
        # and that it is the expected version
        output = StringIO()
        self.run("pkgconf --about", output, env="conanbuild")
        # TODO: When recipe is Conan 2+ only, this can be simplified
        # to: self.dependencies['pkgconf'].ref.version
        tokens = re.split('[@#]', self.tested_reference_str)
        pkgconf_expected_version = tokens[0].split("/", 1)[1]
        assert f"pkgconf {pkgconf_expected_version}" in output.getvalue()

        # Test that executable linked against library runs as expected
        if can_run(self) and self._testing_library:
            test_executable = unix_path(self, os.path.join(self.cpp.build.bindirs[0], "test_package"))
            self.run(test_executable, env="conanrun")

        # Cleanup the configuration ariifacts
        artifacts = "autom4te.cache", "aclocal.m4", "configure", "configure~"
        for artifact in artifacts:
            try:
                self.output.info(f"Removing {artifact} from {self.source_folder}")
                full_path = os.path.join(self.source_folder, artifact)
                if os.path.isfile(full_path):
                    rm(self, artifact, self.source_folder)
                else:
                    rmdir(self, full_path)
            except Exception as e:
                self.output.error(f"Failed to remove {artifact}: {e}")

