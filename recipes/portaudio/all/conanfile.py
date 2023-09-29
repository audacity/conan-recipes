import os
import shutil

from conan import ConanFile
from conan.tools.files import export_conandata_patches, apply_conandata_patches, get, rmdir, copy, collect_libs
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout

required_conan_version = ">=2.0.0"
class ConanRecipe(ConanFile):
    name = "portaudio"
    settings = "os", "compiler", "build_type", "arch"
    description = "Conan package for the Portaudio library"
    url = "https://github.com/audacity/conan-recipes"
    license = "http://www.portaudio.com/license.html"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        # Windows specific options:
        "with_asio": [True, False],
        "with_directsound": [True, False],
        "with_mme": [True, False],
        "with_wasapi": [True, False],
        "with_wdmks": [True, False],
        "with_static_runtime": [True, False],
        # *nix specific options:
        "with_oss": [True, False],
        "with_alsa":  [True, False],
        "with_alsa_dynamic":  [True, False],
        "with_jack":  [True, False],
        # macOS specific options:
        "build_framework":  [True, False],
    }

    default_options = {
        'shared': False,
        'fPIC': True,
        "with_asio": False,
        "with_directsound": True,
        "with_mme": True,
        "with_wasapi": True,
        "with_wdmks": True,
        "with_static_runtime": False,
        "with_oss": True,
        "with_alsa":  True,
        "with_alsa_dynamic":  False,
        "with_jack":  True,
        "build_framework": False,
    }

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        else:
            for opt in [
                "with_asio", "with_directsound", "with_mme",
                "with_wasapi", "with_wdmks", "with_static_runtime"
                ]:
                self.options.rm_safe(opt)

            if self.settings.os == "Macos":
                del self.options.with_oss
                del self.options.with_alsa
                del self.options.with_alsa_dynamic
            else:
                del self.options.build_framework

    def configure(self):
        self.settings.rm_safe('compiler.libcxx')
        self.settings.rm_safe('compiler.cppstd')

    def export_sources(self):
        export_conandata_patches(self)
        copy(self, "FindOSS.cmake", self.recipe_folder, os.path.join(self.export_sources_folder, "cmake_support"))

    def layout(self):
        cmake_layout(self, src_folder=os.path.join('src','portadio'))

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

        if not os.path.exists(os.path.join(self.source_folder, "cmake_support", "FindOSS.cmake")):
           copy(self, "FindOSS.cmake", os.path.join(self.export_sources_folder, "cmake_support"), os.path.join(self.source_folder, "cmake_support"))

    def generate(self):
        if self.options.get_safe('with_asio'):
            self.output.write("ASIO requires that Steinberg ASIO SDK Licensing Agreement Version 2.0.1 is signed\n")

            get(self,
                url="https://download.steinberg.net/sdk_downloads/asiosdk_2.3.3_2019-06-14.zip",
                #sha256="80F5BF2703563F6047ACEC2EDD468D0838C9F61ECED9F7CDCE9629B04E9710AC",
                destination=os.path.realpath(os.path.join(self.source_folder, "..")))

        tc = CMakeToolchain(self)

        tc.variables['PA_BUILD_SHARED'] = self.options.shared
        tc.variables['PA_BUILD_STATIC'] = not self.options.shared

        if self.settings.os == "Windows":
            tc.variables['PA_USE_ASIO'] = self.options.with_asio
            tc.variables['PA_USE_DS'] = self.options.with_directsound
            tc.variables['PA_USE_WMME'] = self.options.with_mme
            tc.variables['PA_USE_WASAPI'] = self.options.with_wasapi
            tc.variables['PA_USE_WDMKS'] = self.options.with_wdmks
            tc.variables['PA_USE_WDMKS_DEVICE_INFO'] = self.options.with_wdmks
            tc.variables['PA_DLL_LINK_WITH_STATIC_RUNTIME'] = self.options.with_static_runtime
        elif self.settings.os == "Macos":
            tc.variables['PA_OUTPUT_OSX_FRAMEWORK'] = self.options.build_framework
        else:
            tc.variables['PA_USE_OSS'] = self.options.with_oss
            tc.variables['PA_USE_JACK'] = self.options.with_jack
            tc.variables['PA_USE_ALSA'] = self.options.with_alsa
            tc.variables['PA_ALSA_DYNAMIC'] = self.options.with_alsa_dynamic

        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

        copy(self,
            "LICENSE.txt",
            dst=os.path.join(self.package_folder, "licenses"),
            src=os.path.join(self.package_folder, "share", "doc", "portaudio")
            )

        rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("cmake_module_file_name", "PortAudio")
        self.cpp_info.set_property("cmake_module_target_name", "portaudio::portaudio")
        self.cpp_info.set_property("cmake_file_name", "PortAudio")
        self.cpp_info.set_property("cmake_target_name", "portaudio::portaudio")
        self.cpp_info.set_property("pkg_config_name", "portaudio-2.0")

        self.cpp_info.libs = collect_libs(self)

        if self.settings.os == "Macos":
            self.cpp_info.frameworks.extend(["CoreAudio","AudioToolbox","AudioUnit","CoreServices","Carbon"])
        elif self.settings.os == "Windows":
            if self.settings.compiler == "gcc" and not self.options.shared:
                self.cpp_info.system_libs.append('winmm')
        else:
            if not self.options.shared:
                self.cpp_info.system_libs.extend(['m', 'pthread'])

                if self.options.with_jack:
                    self.cpp_info.system_libs.append('jack')

                if self.options.with_alsa_dynamic:
                    self.cpp_info.system_libs.append('dl')
                elif self.options.with_alsa:
                    self.cpp_info.system_libs.append('asound')
