from conans import ConanFile, CMake, AutoToolsBuildEnvironment, tools


class BreakpadConan(ConanFile):
    name = "breakpad"
    license = "https://chromium.googlesource.com/breakpad/breakpad/+/refs/heads/master/LICENSE"
    url = "https://github.com/audacity/conan-recipes"
    description = "Breakpad is a set of client and server components which implement a crash-reporting system."
    topics = ("breakpad", "crash-reporting")
    settings = "os", "compiler", "build_type", "arch"
    options = {"fPIC": [True, False]}
    default_options = {"fPIC": True}
    generators = "cmake"
    exports_sources=["CMakeLists.txt", "patches/*"]
    branch = "chrome_90"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def source(self):
        self.run('git clone https://chromium.googlesource.com/breakpad/breakpad --branch %s' %self.branch)
        
        if self.settings.os == 'Linux':
            self.run("git clone https://chromium.googlesource.com/linux-syscall-support breakpad/src/third_party/lss")
        
        if self.settings.os == "Windows":
            tools.patch(base_path="breakpad", patch_file="patches/win-hide-attachment-full-names.diff")

        #TODO: rewrite to cmake configure?
        if self.settings.os == 'Linux' or self.settings.os == 'Macos':
            autotools = AutoToolsBuildEnvironment(self)
            autotools.configure(configure_dir='breakpad')
        
    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):

        self.copy("*.h", dst="include/google_breakpad", src="breakpad/src/google_breakpad")
        self.copy("*.h", dst="include/processor", src="breakpad/src/processor")
        self.copy("*.h", dst="include/client", src="breakpad/src/client")
        self.copy("*.h", dst="include/common", src="breakpad/src/common")
        
        self.copy("*.lib", dst="lib", keep_path=False)
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.components["client"].libs.append("breakpad_client")
        self.cpp_info.components["processor"].libs.append("breakpad_processor")
        self.cpp_info.components["sender"].libs.append("breakpad_sender")
