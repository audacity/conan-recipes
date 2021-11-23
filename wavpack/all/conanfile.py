from conans import ConanFile, tools, CMake
from conans.errors import ConanInvalidConfiguration
import os


class WavPackConan(ConanFile):
    name = "wavpack"
    description = "Hybrid Lossless Wavefile Compressor."
    topics = ("conan", "wavpack", "lossless", "audio", "lossy", "wv")
    url = "https://github.com/audacity/conan-recipes"
    homepage = "https://www.wavpack.com/"
    license = "BSD"
    settings = "os", "arch", "compiler", "build_type"
    generators = ["cmake", "cmake_find_package"]
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "legacy_format": [True, False],
        "enable_dsd" : [True, False]
    }

    default_options = {
        "shared": False,
        "fPIC": True,
        "legacy_format": False,
        "enable_dsd": True
    }

    exports_sources = ["CMakeLists.txt"]

    _cmake = None

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = "wavpack-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake

        cmake = CMake(self)

        cmake.definitions['BUILD_SHARED_LIBS'] = self.options.shared
        cmake.definitions['WAVPACK_ENABLE_LEGACY'] = self.options.legacy_format
        cmake.definitions['WAVPACK_ENABLE_DSD'] = self.options.enable_dsd
        cmake.definitions['WAVPACK_INSTALL_CMAKE_MODULE'] = False
        cmake.definitions['WAVPACK_INSTALL_DOCS'] = False
        cmake.definitions['WAVPACK_INSTALL_PKGCONFIG_MODULE'] = False
        cmake.definitions['WAVPACK_ENABLE_LIBCRYPTO'] = False
        cmake.definitions['WAVPACK_BUILD_PROGRAMS'] = False
        cmake.definitions['WAVPACK_BUILD_COOLEDIT_PLUGIN'] = False
        cmake.definitions['WAVPACK_BUILD_WINAMP_PLUGIN'] = False
        cmake.definitions['BUILD_TESTING'] = False
        cmake.definitions['WAVPACK_BUILD_DOCS'] = False

        cmake.configure(build_folder=self._build_subfolder)

        self._cmake = cmake

        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)

        cmake = self._configure_cmake()
        cmake.install()

    def package_info(self):
        self.cpp_info.name = "WavPack"

        self.cpp_info.libs = self.collect_libs()

