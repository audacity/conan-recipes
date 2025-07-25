from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, rmdir
from conan.tools.microsoft import check_min_vs, is_msvc, is_msvc_static_runtime
from conan.tools.env import VirtualBuildEnv
from conan.tools.scm import Version
import os

required_conan_version = ">=2"


class OpusConan(ConanFile):
    name = "opus"
    description = "Opus is a totally open, royalty-free, highly versatile audio codec."
    topics = ("opus", "audio", "decoder", "decoding", "multimedia", "sound")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://opus-codec.org"
    license = "BSD-3-Clause"
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "fixed_point": [True, False],
        "stack_protector": [True, False],
        "sse4_1": [True, False],
        "avx": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "fixed_point": False,
        "stack_protector": True,
        "sse4_1": False,
        "avx": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        check_min_vs(self, 190)
        if Version(self.version) >= "1.5.2" and self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "8":
            raise ConanInvalidConfiguration(f"{self.ref} GCC-{self.settings.compiler.version} not supported due to lack of AVX2 support. Use GCC >=8.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version],
            destination=self.source_folder, strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.cache_variables["OPUS_BUILD_SHARED_LIBRARY"] = self.options.shared
        tc.cache_variables["OPUS_FIXED_POINT"] = self.options.fixed_point
        tc.cache_variables["OPUS_STACK_PROTECTOR"] = self.options.stack_protector
        tc.cache_variables["OPUS_X86_MAY_HAVE_SSE4_1"] = self.options.sse4_1
        if Version(self.version) <= "1.4.0":
            tc.cache_variables["OPUS_X86_MAY_HAVE_AVX"] = self.options.avx
        else:
            tc.cache_variables["OPUS_X86_MAY_HAVE_AVX2"] = self.options.avx

        if Version(self.version) >= "1.5.2" and is_msvc(self):
            tc.cache_variables["OPUS_STATIC_RUNTIME"] = is_msvc_static_runtime(self)
        if Version(self.version) < "1.5":
            tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5"  # CMake 4 support
        tc.generate()

    def build(self):
        apply_conandata_patches(self)
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "Opus")
        self.cpp_info.set_property("cmake_target_name", "Opus::opus")
        self.cpp_info.set_property("pkg_config_name", "opus")
        # TODO: back to global scope in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.components["libopus"].libs = ["opus"]
        self.cpp_info.components["libopus"].includedirs.append(os.path.join("include", "opus"))
        if self.settings.os in ["Linux", "FreeBSD", "Android"]:
            self.cpp_info.components["libopus"].system_libs.append("m")
        if self.settings.os == "Windows" and self.settings.compiler == "gcc":
            self.cpp_info.components["libopus"].system_libs.append("ssp")

        # TODO: to remove in conan v2 once cmake_find_package_* generators removed
        self.cpp_info.components["libopus"].set_property("cmake_target_name", "Opus::opus")
        self.cpp_info.components["libopus"].set_property("pkg_config_name", "opus")
