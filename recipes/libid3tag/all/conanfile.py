from conan import ConanFile, tools
from conan.tools.cmake import CMake, cmake_layout, CMakeToolchain, CMakeDeps
from conan.errors import ConanInvalidConfiguration
import os

class LibId3TagConan(ConanFile):
    name = "libid3tag"
    description = "ID3 tag manipulation library."
    topics = ("conan", "mad", "id3", "MPEG", "audio", "decoder")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.underbit.com/products/mad/"
    license = "GPL-2.0-or-later"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False], "zlib": ["system", "conan"]}
    default_options = {"shared": False, "fPIC": True, "zlib": "conan"}

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def validate(self):
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration("libid3tag does not support shared library for Windows")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.zlib == "conan":
            self.requires("zlib/1.2.13@audacity/stable")

    def source(self):
        tools.files.get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables['BUILD_SHARED'] = self.options.shared
        tc.generate()

        cd = CMakeDeps(self)
        cd.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        tools.files.copy(self, pattern="COPYRIGHT", src=self.source_folder, dst=os.path.join(self.package_folder,"licenses"))
        tools.files.copy(self, pattern="COPYING", src=self.source_folder, dst=os.path.join(self.package_folder,"licenses"))
        tools.files.copy(self, pattern="CREDITS", src=self.source_folder, dst=os.path.join(self.package_folder,"licenses"))

        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["libid3tag"]
