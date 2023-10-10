import os

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.layout import basic_layout
from conan.tools.meson import Meson
from conan.tools.files import rm


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "MesonToolchain", "VirtualBuildEnv", "VirtualRunEnv"
    test_type = "explicit"
    meson_dirs = []

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def layout(self):
        basic_layout(self)

    def build(self):
        meson = Meson(self)
        meson.configure()
        meson.build()

        self.meson_dirs = self.dependencies.build['meson'].cpp_info.bindirs

    def test(self):
        self.run("meson --version")
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindirs[0], "test_package")
            self.run(bin_path, env="conanrun")

            for meson_dir in self.meson_dirs:
                self.output.info("Removing .pyc files from {}".format(meson_dir))
                for i in range(20):
                    try:
                        rm(self, "*.pyc", meson_dir, recursive=True)
                        break
                    except:
                        self.output.error("Failed to remove .pyc files from {}".format(meson_dir))
                        import time
                        time.sleep(0.1 * i)
