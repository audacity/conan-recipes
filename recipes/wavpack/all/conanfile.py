import os
from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import get, export_conandata_patches, apply_conandata_patches, copy, collect_libs

class WavPackConan(ConanFile):
    name = "wavpack"
    description = "Hybrid Lossless Wavefile Compressor."
    topics = ("conan", "wavpack", "lossless", "audio", "lossy", "wv")
    url = "https://github.com/audacity/conan-recipes"
    homepage = "https://www.wavpack.com/"
    license = "BSD"
    settings = "os", "arch", "compiler", "build_type"
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


    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables['BUILD_SHARED_LIBS'] = self.options.shared
        tc.cache_variables['WAVPACK_ENABLE_LEGACY'] = self.options.legacy_format
        tc.cache_variables['WAVPACK_ENABLE_DSD'] = self.options.enable_dsd
        tc.cache_variables['WAVPACK_INSTALL_CMAKE_MODULE'] = False
        tc.cache_variables['WAVPACK_INSTALL_DOCS'] = False
        tc.cache_variables['WAVPACK_INSTALL_PKGCONFIG_MODULE'] = False
        tc.cache_variables['WAVPACK_ENABLE_LIBCRYPTO'] = False
        tc.cache_variables['WAVPACK_BUILD_PROGRAMS'] = False
        tc.cache_variables['WAVPACK_BUILD_COOLEDIT_PLUGIN'] = False
        tc.cache_variables['WAVPACK_BUILD_WINAMP_PLUGIN'] = False
        tc.cache_variables['BUILD_TESTING'] = False
        tc.cache_variables['WAVPACK_BUILD_DOCS'] = False
        tc.generate()


    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", dst=os.path.join(self.package_folder, "licenses"), src=self.source_folder)

        cmake = CMake(self)
        cmake.install()

        # On Linux, header gets installed to $prefix/include/wavpack/wavpack.h
        # Let's duplicate this behavior
        copy(self, "*.h", dst=os.path.join(self.package_folder, 'include', 'wavpack'), src=os.path.join(self.source_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_module_file_name", "WavPack")
        self.cpp_info.set_property("cmake_module_target_name", "wavpack::wavpack")
        self.cpp_info.set_property("cmake_file_name", "WavPack")
        self.cpp_info.set_property("cmake_target_name", "wavpack::wavpack")
        self.cpp_info.set_property("pkg_config_name", "wavpack")

        self.cpp_info.libs = collect_libs(self)

