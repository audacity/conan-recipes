from conans import ConanFile, tools, CMake
from conans.errors import ConanInvalidConfiguration
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
    generators = ["cmake", "cmake_find_package"]

    exports_sources = ["CMakeLists.txt"]

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd
        if self.settings.os == "Windows" and self.options.shared:
            raise ConanInvalidConfiguration("libid3tag does not support shared library for Windows")

    def requirements(self):
        if self.options.zlib == "conan":
            self.requires("zlib/1.2.11")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)


    def _configure_cmake(self):
        if self._cmake:
            return self._cmake

        cmake = CMake(self)

        cmake.definitions['BUILD_SHARED'] = self.options.shared

        cmake.configure(build_folder=self._build_subfolder)

        self._cmake = cmake

        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("COPYRIGHT", dst="licenses", src=self._source_subfolder)
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        self.copy("CREDITS", dst="licenses", src=self._source_subfolder)
        
        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["libid3tag"]
