from conans import ConanFile, tools, CMake
from conans.errors import ConanInvalidConfiguration
import os


class LibmadConan(ConanFile):
    name = "libmad"
    description = "MAD is a high-quality MPEG audio decoder.format."
    topics = ("conan", "mad", "MPEG", "audio", "decoder")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://www.underbit.com/products/mad/"
    license = "GPL-2.0-or-later"
    settings = "os", "arch", "compiler", "build_type"
    generators = ["cmake", "cmake_find_package"]
    options = {
        "shared": [True, False], 
        "fPIC": [True, False], 
        "opt_accuracy": [True, False], 
        "opt_speed": [True, False], 
        "opt_sso": [True, False]
    }

    default_options = {
        "shared": False, 
        "fPIC": True, 
        "opt_accuracy": True, 
        "opt_speed": False, 
        "opt_sso": False
    }

    exports_sources = ["CMakeLists.txt"]

    _cmake = None

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd
        if self.settings.os == 'Windows' and self.options.shared:
            raise ConanInvalidConfiguration("libmad does not support shared library for Windows")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake

        cmake = CMake(self)

        cmake.definitions['BUILD_SHARED'] = self.options.shared
        cmake.definitions['OPT_ACCURACY'] = self.options.opt_accuracy
        cmake.definitions['OPT_SPEED'] = self.options.opt_speed
        cmake.definitions['OPT_SSO'] = self.options.opt_sso

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
        self.cpp_info.libs = ["libmad"]
