import os
import shutil

from conans import ConanFile, CMake, tools

class ConanRecipe(ConanFile):
    name = "portaudio"
    settings = "os", "compiler", "build_type", "arch"
    generators = ["cmake"]
    sources_folder = "sources"
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
    exports = ["CMakeLists.txt"]
    exports_sources = ["patches/19.7.0/*"]

    _cmake = None
    _build_folder = "build_folder"

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

        if self.settings.os == "Windows":
            self.options.remove("fPIC")
        else:
            for opt in [
                "with_asio", "with_directsound", "with_mme", 
                "with_wasapi", "with_wdmks", "with_static_runtime"
                ]:
                self.options.remove(opt)
            
            if self.settings.os == "Macos":
                self.options.remove("with_oss")
                self.options.remove("with_alsa")
                self.options.remove("with_alsa_dynamic")
                self.options.remove("with_jack") 
            else:
                self.options.remove("build_framework") 

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("portaudio", self.sources_folder)

        if "patches" in self.conan_data:
            for p in self.conan_data["patches"][self.version]:
                tools.patch(**p)

        if self.settings.os == "Windows" and self.options.with_asio:
            # ASIO requires that Steinberg ASIO SDK Licensing Agreement Version 2.0.1
            # is signed
            tools.get(
                url="https://download.steinberg.net/sdk_downloads/asiosdk_2.3.3_2019-06-14.zip", 
                sha256="80F5BF2703563F6047ACEC2EDD468D0838C9F61ECED9F7CDCE9629B04E9710AC"
            )

        if self.settings.os != "Windows" and self.settings.os != "Macos":
            shutil.copyfile("patches/19.7.0/FindOSS.cmake", os.path.join(self.sources_folder, "cmake_support", "FindOSS.cmake"))

    def _cmake_configure(self):
        if not self._cmake:
            cmake = CMake(self)

            cmake.definitions['PA_BUILD_SHARED'] = self.options.shared
            cmake.definitions['PA_BUILD_STATIC'] = not self.options.shared

            if self.settings.os == "Windows":
                cmake.definitions['PA_USE_ASIO'] = self.options.with_asio
                cmake.definitions['PA_USE_DS'] = self.options.with_directsound
                cmake.definitions['PA_USE_WMME'] = self.options.with_mme
                cmake.definitions['PA_USE_WASAPI'] = self.options.with_wasapi
                cmake.definitions['PA_USE_WDMKS'] = self.options.with_wdmks
                cmake.definitions['PA_USE_WDMKS_DEVICE_INFO'] = self.options.with_wdmks
                cmake.definitions['PA_DLL_LINK_WITH_STATIC_RUNTIME'] = self.options.with_static_runtime
            elif self.settings.os == "Macos":
                cmake.definitions['PA_OUTPUT_OSX_FRAMEWORK'] = self.options.build_framework
            else:
                cmake.definitions['PA_USE_OSS'] = self.options.with_oss
                cmake.definitions['PA_USE_JACK'] = self.options.with_jack
                cmake.definitions['PA_USE_ALSA'] = self.options.with_alsa
                cmake.definitions['PA_ALSA_DYNAMIC'] = self.options.with_alsa_dynamic

            cmake.configure(build_folder=self._build_folder)
            self._cmake = cmake

        return self._cmake
            
    def build(self):
        cmake = self._cmake_configure()
        cmake.build()

    def package(self):
        cmake = self._cmake_configure()
        cmake.install()

        self.copy(
            "LICENSE.txt", 
            dst="licenses", 
            src=os.path.join(self.package_folder, "share", "doc", "portaudio")
            )

        shutil.rmtree(os.path.join(self.package_folder, "share"))
        shutil.rmtree(os.path.join(self.package_folder, "lib", "cmake"))
        shutil.rmtree(os.path.join(self.package_folder, "lib", "pkgconfig"))
        
    def package_info(self):
        self.cpp_info.name = "PortAudio"

        self.cpp_info.libs = tools.collect_libs(self)

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
