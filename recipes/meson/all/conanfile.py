import os
import textwrap

from conan import ConanFile, conan_version
from conan.tools.files import copy, get, rmdir, save, rm
from conan.tools.layout import basic_layout
from conan.tools.scm import Version

required_conan_version = ">=1.52.0"


class MesonConan(ConanFile):
    name = "meson"
    package_type = "application"
    description = "Meson is a project to create the best possible next-generation build system"
    topics = ("meson", "mesonbuild", "build-system")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/mesonbuild/meson"
    license = "Apache-2.0"
    no_copy_source = True

    def layout(self):
        basic_layout(self, src_folder="src")
        self.folders.build = 'build'
        self.folders.generators = 'build/conan'

    def requirements(self):
        if self.conf.get("tools.meson.mesontoolchain:backend", default="ninja", check_type=str) == "ninja":
            self.requires("ninja/1.11.0@audacity/stable")

    def package_id(self):
        self.info.clear()

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def build(self):
        pass

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "*", src=self.source_folder, dst=os.path.join(self.package_folder, "bin"))

        for i in range(20):
            try:
                self.output.info("Removing test cases from {}".format(os.path.join(self.package_folder, "bin")))
                rmdir(self, os.path.join(self.package_folder, "bin", "test cases"))
                break
            except:
                self.output.error("Failed to remove test cases from {}".format(os.path.join(self.package_folder, "bin")))
                import time
                time.sleep(0.1 * i)

        for i in range(20):
            try:
                self.output.info("Removing .pyc files from {}".format(os.path.join(self.package_folder, "bin")))
                rm(self, "*.pyc", base_path=os.path.join(self.package_folder, "bin"), recursive=True)
                break
            except:
                self.output.error("Failed to remove .pyc files from {}".format(os.path.join(self.package_folder, "bin")))
                import time
                time.sleep(0.1 * i)

        # create wrapper scripts
        save(self, os.path.join(self.package_folder, "bin", "meson.cmd"), textwrap.dedent("""\
            @echo off
            CALL python %~dp0/meson.py %*
        """))
        save(self, os.path.join(self.package_folder, "bin", "meson"), textwrap.dedent("""\
            #!/usr/bin/env bash
            meson_dir=$(dirname "$0")
            exec "$meson_dir/meson.py" "$@"
        """))

    @staticmethod
    def _chmod_plus_x(filename):
        if os.name == "posix":
            os.chmod(filename, os.stat(filename).st_mode | 0o111)

    def package_info(self):
        meson_root = os.path.join(self.package_folder, "bin")
        self._chmod_plus_x(os.path.join(meson_root, "meson"))
        self._chmod_plus_x(os.path.join(meson_root, "meson.py"))

        self.cpp_info.builddirs = [os.path.join("bin", "mesonbuild", "cmake", "data")]

        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []

        if Version(conan_version).major < 2:
            self.env_info.PATH.append(meson_root)
