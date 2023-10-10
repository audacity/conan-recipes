from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.files import rm
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "VirtualBuildEnv"
    test_type = "explicit"

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def test(self):
        self.run("nasm --version")
        asm_file = os.path.join(self.source_folder, "hello_linux.asm")
        out_file = os.path.join(self.build_folder, "hello_linux.o")
        self.run(f"nasm -felf64 {asm_file} -o {out_file}")
        if can_run(self):
            if self.settings.os == "Linux" and self.settings.arch == "x86_64":
                # TODO was tools.get_env, what should it be?
                ld = os.getenv("LD", "ld")
                bin_file = os.path.join(self.build_folder, "hello_linux")
                self.run(f"{ld} hello_linux.o -o {bin_file}")
                self.run(bin_file)

        # Clean up
        rm(self, '*conanbuild*', self.source_folder)
        rm(self, '*conanrun*', self.source_folder)
        rm(self, 'hello_linux.o', self.source_folder)
