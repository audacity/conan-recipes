from conan import ConanFile, tools
from conan.tools.cmake import cmake_layout
from conan.errors import ConanInvalidConfiguration
from conan.tools.env import Environment
from contextlib import contextmanager
import conan.tools.files as tools_files
import conan.tools.scm as tools_scm
import os
import sys
import textwrap
import time

required_conan_version = ">=1.46.0"


class GnConan(ConanFile):
    name = "gn"
    description = "GN is a meta-build system that generates build files for Ninja."
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("gn", "build", "system", "ninja")
    license = "BSD-3-Clause"
    homepage = "https://gn.googlesource.com/"
    settings = "os", "arch", "compiler", "build_type"
    generators = "VCVars"

    @property
    def _minimum_compiler_version_supporting_cxx17(self):
        return {
            "msvc": 170,
            "gcc": 7,
            "clang": 4,
            "apple-clang": 10,
        }.get(str(self.settings.compiler))

    def validate(self):
        if self.settings.compiler.cppstd:
            tools.build.check_min_cppstd(self, 17)
        else:
            if self._minimum_compiler_version_supporting_cxx17:
                if tools_scm.Version(self.settings.compiler.version) < self._minimum_compiler_version_supporting_cxx17:
                    raise ConanInvalidConfiguration("gn requires a compiler supporting c++17")
            else:
                self.output.warn("gn recipe does not recognize the compiler. gn requires a compiler supporting c++17. Assuming it does.")

    def package_id(self):
        del self.info.settings.compiler

    def source(self):
        tools_files.get(self, **self.conan_data["sources"][self.version], destination=self.source_folder)

    def build_requirements(self):
        # FIXME: add cpython build requirements for `build/gen.py`.
        self.build_requires("ninja/1.11.0@audacity/stable")

    def layout(self):
        cmake_layout(self, src_folder="src")

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

    def _to_gn_platform(self):
        if tools.apple.is_apple_os(self):
            return "darwin"
        if self.settings.compiler == "msvc":
            return "msvc"
        # Assume gn knows about the os
        return str(self.settings.os).lower()

    def build(self):
        with tools.files.chdir(self, self.source_folder):
            with self._build_context():
                # Generate dummy header to be able to run `build/ben.py` with `--no-last-commit-position`. This allows running the script without the tree having to be a git checkout.
                tools.files.save(self, os.path.join("src", "gn", "last_commit_position.h"),
                           textwrap.dedent("""\
                                #pragma once
                                #define LAST_COMMIT_POSITION "1"
                                #define LAST_COMMIT_POSITION_NUM 1
                                """))
                conf_args = [
                    "--no-last-commit-position",
                    "--host={}".format(self._to_gn_platform()),
                ]
                if self.settings.build_type == "Debug":
                    conf_args.append("-d")
                self.run("{} build/gen.py {}".format(sys.executable, " ".join(conf_args)))
                # Try sleeping one second to avoid time skew of the generated ninja.build file (and having to re-run build/gen.py)
                time.sleep(1)
                build_args = [
                    "-C", "out",
                    "-j{}".format(tools.build.build_jobs(self)),
                ]
                self.run("ninja {}".format(" ".join(build_args)))

    def package(self):
        tools.files.copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder,"licenses"))
        tools.files.copy(self, "gn", src=os.path.join(self.source_folder, "out"), dst=os.path.join(self.package_folder,"bin"))
        tools.files.copy(self, "gn.exe", src=os.path.join(self.source_folder, "out"), dst=os.path.join(self.package_folder,"bin"))

    def package_info(self):
        bin_path = os.path.join(self.package_folder, "bin")
        self.output.info("Appending PATH environment variable: {}".format(bin_path))
        self.env_info.PATH.append(bin_path)
        self.cpp_info.includedirs = []
