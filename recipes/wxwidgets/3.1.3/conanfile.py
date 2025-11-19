from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.system.package_manager import Apt, Dnf, PacMan
from conan.tools.files import get, export_conandata_patches, apply_conandata_patches, copy
from conan.tools.gnu import PkgConfig

import os

required_conan_version = ">=2.0.0"

class wxWidgetsConan(ConanFile):
    name = "wxwidgets"
    description = "wxWidgets is a C++ library that lets developers create applications for Windows, macOS, " \
                  "Linux and other platforms with a single code base."
    topics = ("conan", "wxwidgets", "gui", "ui")
    url = "https://github.com/bincrafters/conan-wxwidgets"
    homepage = "https://www.wxwidgets.org"
    license = "wxWidgets"
    settings = "os", "arch", "compiler", "build_type"

    # 3rd-party dependencies
    #
    # Specify "sys" if you want CMake to find_package for a dependency
    # which was installed outside of Conan.
    #
    # Specify one of the library names such as "libjpeg-turbo" if you
    # want Conan to obtain that library, and have CMake use that via find_package.
    #
    # In either case, the string "sys" will be passed to CMake in the configure step
    #
    # Specify "off" to compile without support for a particular library/format
    #
    # This package is intentionally not capable of using the git submodules.
    # It gets sources from github release, which do not include submodule content.
    # For this reason, "builtin" is not a valid value for these options when using Conan.

    # TODO: Get rid of the "sys" options
    options = {"shared": [True, False],
               "fPIC": [True, False],
               "unicode": [True, False],
               "compatibility": ["2.8", "3.0", "3.1"],
               "zlib": ["off", "sys", "zlib"],
               "png": ["off", "sys", "libpng"],
               "jpeg": ["off", "sys", "libjpeg-turbo"],
               "tiff": ["off", "sys", "libtiff"],
               "expat": ["off", "sys", "expat"],
               "secretstore": [True, False],
               "aui": [True, False],
               "opengl": [True, False],
               "html": [True, False],
               "mediactrl": [True, False],  # disabled by default as wxWidgets still uses deprecated GStreamer 0.10
               "propgrid": [True, False],
               "debugreport": [True, False],
               "ribbon": [True, False],
               "richtext": [True, False],
               "sockets": [True, False],
               "stc": [True, False],
               "webview": [True, False],
               "xml": [True, False],
               "xrc": [True, False],
               "cairo": [True, False],
               "help": [True, False],
               "html_help": [True, False],
               "url": [True, False],
               "protocol": [True, False],
               "fs_inet": [True, False],
               "custom_enables": ["ANY"], # comma splitted list
               "custom_disables": ["ANY"]}
    default_options = {
               "shared": False,
               "fPIC": True,
               "unicode": True,
               "compatibility": "3.0",
               "zlib": "zlib",
               "png": "libpng",
               "jpeg": "libjpeg-turbo",
               "tiff": "libtiff",
               "expat": "expat",
               "secretstore": True,
               "aui": True,
               "opengl": True,
               "html": True,
               "mediactrl": False,
               "propgrid": True,
               "debugreport": True,
               "ribbon": True,
               "richtext": True,
               "sockets": True,
               "stc": True,
               "webview": False,
               "xml": True,
               "xrc": True,
               "cairo": True,
               "help": True,
               "html_help": True,
               "url": True,
               "protocol": True,
               "fs_inet": True,
               "custom_enables": "",
               "custom_disables": ""
    }

    @property
    def _is_msvc(self):
        return is_msvc(self)

    @property
    def _is_linux(self):
        return self.settings.os not in ["Windows", "Macos"]

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC
        if self.settings.os != 'Linux':
            del self.options.cairo

    def system_requirements(self):
        apt = Apt(self)
        dnf = Dnf(self)
        pacman = PacMan(self)

        apt.check(['libx11-dev'])
        dnf.check(['libX11-devel'])
        pacman.check(['libx11'])

        apt.check(['libgtk2.0-dev'])
        dnf.check(['gtk2-devel'])
        pacman.check(['gtk2'])

        if self.options.secretstore:
            apt.check(['libsecret-1-dev'])
            dnf.check(['libsecret-devel'])
            pacman.check(['libsecret'])
        if self.options.opengl:
            apt.check(['libgl1-mesa-dev', 'mesa-common-dev'])
            dnf.check(['mesa-libGL-devel', 'mesa-libGLU-devel'])
            pacman.check(['mesa', 'glu'])

        if self.options.webview:
            apt.check(['libwebkitgtk-dev', 'libsoup2.4-dev'])
            dnf.check(['webkitgtk2-devel', 'libsoup-devel'])
            pacman.check(['webkitgtk', 'libsoup'])

        if self.options.mediactrl:
            apt.check(['libgstreamer0.10-dev', 'libgstreamer-plugins-base0.10-dev'])
            dnf.check(['gstreamer-devel', 'gstreamer-plugins-base-devel'])
            pacman.check(['gstreamer', 'gstreamer-plugins-base'])

        if self.options.get_safe('cairo'):
            apt.check(['libcairo2-dev'])
            dnf.check(['cairo-devel'])
            pacman.check(['cairo'])

    def build_requirements(self):
        # On Windows, use default build system.
        # MSVC works good anyway, but Ninja
        # won't work on Cygwin setups.
        if self.settings.os != "Windows":
            self.build_requires("ninja/1.11.0@audacity/stable")

    def requirements(self):
        if self.options.png == 'libpng':
            self.requires("libpng/[>=1.6.39 <1.7]@audacity/stable")
        if self.options.jpeg == 'libjpeg-turbo':
            self.requires('libjpeg-turbo/2.1.5@audacity/stable')
        if self.options.tiff == 'libtiff':
            self.requires('libtiff/4.5.0@audacity/stable')
        if self.options.zlib == 'zlib':
            self.requires("zlib/[>=1.2.13 <1.4]@audacity/stable")
        if self.options.expat == 'expat' and self.options.xml:
            self.requires('expat/2.5.0@audacity/stable')

    def export_sources(self):
        export_conandata_patches(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)

        tc.variables['wxBUILD_SHARED'] = self.options.shared
        tc.variables['wxBUILD_SAMPLES'] = 'OFF'
        tc.variables['wxBUILD_TESTS'] = 'OFF'
        tc.variables['wxBUILD_DEMOS'] = 'OFF'
        tc.variables['wxBUILD_INSTALL'] = True
        tc.variables['wxBUILD_COMPATIBILITY'] = self.options.compatibility
        if self.settings.compiler == 'clang' or self.settings.compiler == 'apple-clang':
            tc.variables['wxBUILD_PRECOMP'] = 'OFF'

        # platform-specific options
        if self._is_msvc:
            tc.variables['wxBUILD_USE_STATIC_RUNTIME'] = is_msvc_static_runtime(self)
            tc.variables['wxBUILD_MSVC_MULTIPROC'] = True
        if self._is_linux:
            # TODO : GTK3
            # cmake.definitions['wxBUILD_TOOLKIT'] = 'gtk3'
            tc.variables['wxUSE_CAIRO'] = self.options.get_safe('cairo')
        # Disable some optional libraries that will otherwise lead to non-deterministic builds
        if self.settings.os != "Windows":
            tc.variables['wxUSE_LIBSDL'] = 'OFF'
            tc.variables['wxUSE_LIBICONV'] = 'OFF'
            tc.variables['wxUSE_LIBNOTIFY'] = 'OFF'
            tc.variables['wxUSE_LIBMSPACK'] = 'OFF'
            tc.variables['wxUSE_LIBGNOMEVFS'] = 'OFF'

        tc.variables['wxUSE_LIBPNG'] = 'sys' if self.options.png != 'off' else 'OFF'
        tc.variables['wxUSE_LIBJPEG'] = 'sys' if self.options.jpeg != 'off' else 'OFF'
        tc.variables['wxUSE_LIBTIFF'] = 'sys' if self.options.tiff != 'off' else 'OFF'
        tc.variables['wxUSE_ZLIB'] = 'sys' if self.options.zlib != 'off' else 'OFF'
        tc.variables['wxUSE_EXPAT'] = 'sys' if self.options.expat != 'off' else 'OFF'

        # wxWidgets features
        tc.variables['wxUSE_UNICODE'] = self.options.unicode
        tc.variables['wxUSE_SECRETSTORE'] = self.options.secretstore

        # wxWidgets libraries
        tc.variables['wxUSE_AUI'] = self.options.aui
        tc.variables['wxUSE_OPENGL'] = self.options.opengl
        tc.variables['wxUSE_HTML'] = self.options.html
        tc.variables['wxUSE_MEDIACTRL'] = self.options.mediactrl
        tc.variables['wxUSE_PROPGRID'] = self.options.propgrid
        tc.variables['wxUSE_DEBUGREPORT'] = self.options.debugreport
        tc.variables['wxUSE_RIBBON'] = self.options.ribbon
        tc.variables['wxUSE_RICHTEXT'] = self.options.richtext
        tc.variables['wxUSE_SOCKETS'] = self.options.sockets
        tc.variables['wxUSE_STC'] = self.options.stc
        tc.variables['wxUSE_WEBVIEW'] = self.options.webview
        tc.variables['wxUSE_XML'] = self.options.xml
        tc.variables['wxUSE_XRC'] = self.options.xrc
        tc.variables['wxUSE_HELP'] = self.options.help
        tc.variables['wxUSE_WXHTML_HELP'] = self.options.html_help
        tc.variables['wxUSE_URL'] = self.options.protocol
        tc.variables['wxUSE_PROTOCOL'] = self.options.protocol
        tc.variables['wxUSE_FS_INET'] = self.options.fs_inet

        if self.settings.os == "Windows" or self.settings.os == "Macos":
            tc.variables['wxUSE_ACCESSIBILITY'] = True

        for item in str(self.options.custom_enables).split(","):
            if len(item) > 0:
                tc.variables[item] = True
        for item in str(self.options.custom_disables).split(","):
            if len(item) > 0:
                tc.variables[item] = False

        tc.cache_variables["CMAKE_CONFIGURATION_TYPES"] = "Release;Debug;MinSizeRel;RelWithDebInfo"
        tc.cache_variables["CMAKE_POLICY_VERSION_MINIMUM"] = "3.5" # CMake 4 support

        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def layout(self):
        cmake_layout(self, src_folder='src')

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "licence.txt", dst=os.path.join(self.package_folder, "licenses"), src=os.path.join(self.source_folder, "docs"))
        CMake(self).install()
        # copy setup.h
        copy(self, '*setup.h', dst=os.path.join(self.package_folder, 'include', 'wx'), src=os.path.join(self.build_folder, 'lib'),
                  keep_path=False)

        if self.settings.os == 'Windows':
            # copy wxrc.exe
            copy(self, '*.exe', dst=os.path.join(self.package_folder, 'bin'), src=os.path.join(self.build_folder, 'bin'), keep_path=False)
        else:
            # make relative symlink
            bin_dir = os.path.join(self.package_folder, 'bin')
            for x in os.listdir(bin_dir):
                filename = os.path.join(bin_dir, x)
                if os.path.islink(filename):
                    target = os.readlink(filename)
                    if os.path.isabs(target):
                        rel = os.path.relpath(target, bin_dir)
                        os.remove(filename)
                        os.symlink(rel, filename)

    def add_libraries_from_pc(self, lib, cpp_info):
        pc = PkgConfig(self, lib)

        cpp_info.system_libs += pc.libs
        cpp_info.libdirs += pc.libdirs
        cpp_info.sharedlinkflags += pc.linkflags
        cpp_info.exelinkflags += pc.linkflags
        cpp_info.defines += pc.defines
        cpp_info.includedirs += pc.includedirs
        cpp_info.cflags += pc.cflags
        cpp_info.cxxflags += pc.cflags

    @property
    def __defines(self):
        defines = [ 'wxUSE_GUI=1' ]

        if self.settings.build_type == 'Debug':
            defines.append('__WXDEBUG__')

        if self.options.shared:
            defines.append('WXUSINGDLL')

        if self.settings.os == 'Macos':
            defines.extend(['__WXMAC__', '__WXOSX__', '__WXOSX_COCOA__'])
        elif self.settings.os == 'Windows':
            defines.extend([
                '__WXMSW__',
                'wxNO_NET_LIB', 'wxNO_XML_LIB', 'wxNO_REGEX_LIB', 'wxNO_ZLIB_LIB', 'wxNO_JPEG_LIB', 'wxNO_PNG_LIB',
                'wxNO_TIFF_LIB', 'wxNO_ADV_LIB', 'wxNO_HTML_LIB', 'wxNO_GL_LIB', 'wxNO_QA_LIB', 'wxNO_XRC_LIB',
                'wxNO_AUI_LIB', 'wxNO_PROPGRID_LIB', 'wxNO_RIBBON_LIB', 'wxNO_RICHTEXT_LIB',
                'wxNO_MEDIA_LIB', 'wxNO_STC_LIB', 'wxNO_WEBVIEW_LIB'])
        else:
            defines.append('__WXGTK__')

        return defines

    @property
    def __version(self):
        return tuple(map(int, self.version[0:self.version.find('-')].split('.')))

    @property
    def __includedirs(self):
        if self._is_msvc:
            return ['include', 'include/msvc']
        else:
            return ['include', f'include/wx-{self.__version[0]}.{self.__version[1]}']

    def package_info(self):
        version_major = self.__version[0]
        version_minor = self.__version[1]
        version_suffix_major_minor = f'-{version_major}.{version_minor}'
        unicode = 'u' if self.options.unicode else ''

        # wx no longer uses a debug suffix for non-windows platforms from 3.1.3 onwards
        use_debug_suffix = False
        if self.settings.build_type == 'Debug':
            use_debug_suffix = (self.settings.os == 'Windows' or self.__version < (3, 1, 3))

        debug = 'd' if use_debug_suffix else ''

        if self.settings.os == 'Macos':
            prefix = 'wx_'
            toolkit = 'osx_cocoa'
            version = ''
            suffix = version_suffix_major_minor
        elif self.settings.os == 'Windows':
            prefix = 'wx'
            toolkit = 'msw'
            version = f'{version_major}{version_minor}'
            suffix = ''
        else:
            prefix = 'wx_'
            toolkit = 'gtk2'
            version = ''
            suffix = version_suffix_major_minor

        def base_library_pattern(library):
            return '{prefix}base{version}{unicode}{debug}_%s{suffix}' % library

        def library_pattern(library):
            return '{prefix}{toolkit}{version}{unicode}{debug}_%s{suffix}' % library

        def add_component(name, libpattern, requires):
            libname = libpattern.format(prefix=prefix, toolkit=toolkit,
                                        version=version, unicode=unicode,
                                        debug=debug, suffix=suffix
                                        )

            self.cpp_info.components[name].libs = [libname]

            if requires and len(requires) > 0:
                self.cpp_info.components[name].requires = requires

            self.cpp_info.components[name].defines = self.__defines
            self.cpp_info.components[name].includedirs = self.__includedirs

            if self.settings.os == 'Windows':
                # see cmake/init.cmake
                compiler_prefix = {
                    'msvc': 'vc',
                    'gcc': 'gcc',
                    'clang': 'clang'}.get(str(self.settings.compiler))

                if self.settings.arch == 'x86_64':
                    arch_suffix = '_x64'
                elif self.settings.arch == 'armv8':
                    arch_suffix = '_arm64'
                else:
                    arch_suffix = ''
                lib_suffix = '_dll' if self.options.shared else '_lib'
                libdir = '%s%s%s' % (compiler_prefix, arch_suffix, lib_suffix)
                libdir = f'lib/{libdir}'

                self.cpp_info.components[name].bindirs = ['bin', libdir]
                self.cpp_info.components[name].libdirs = ['lib', libdir]

        if not self.options.shared:
            regexLibPattern = 'wxregex{unicode}{debug}' if self.settings.os == "Windows" else 'wxregex{unicode}{debug}{suffix}'
            add_component('regex', regexLibPattern, [])

        add_component('base', '{prefix}base{version}{unicode}{debug}{suffix}', [])
        add_component('core', library_pattern('core'), ['base'])
        add_component('adv', library_pattern('adv'), ['base'])

        if not self.options.shared:
            self.cpp_info.components['core'].requires.append('regex')
        if self.options.png == 'libpng':
            self.cpp_info.components['core'].requires.append('libpng::libpng')
        if self.options.jpeg == 'libjpeg-turbo':
            self.cpp_info.components['core'].requires.append('libjpeg-turbo::libjpeg-turbo')
        if self.options.tiff == 'libtiff':
            self.cpp_info.components['core'].requires.append('libtiff::libtiff')
        if self.options.zlib == 'zlib':
            self.cpp_info.components['base'].requires.append('zlib::zlib')

        if self.options.sockets:
            add_component('net', base_library_pattern('net'), ['base'])
        if self.options.xml:
            add_component('xml', base_library_pattern('xml'), ['base'])

            if self.options.expat == 'expat':
                self.cpp_info.components['xml'].requires.append('expat::expat')

        if self.options.html:
            add_component('html', library_pattern('html'), ['core'])
        if self.options.aui:
            add_component('aui', library_pattern('aui'), ['core', 'html', 'xml'])
        if self.options.opengl:
            add_component('gl', library_pattern('gl'), ['core'])
        if self.options.mediactrl:
            add_component('media', library_pattern('media'), ['core'])
        if self.options.propgrid:
            add_component('propgrid', library_pattern('propgrid'), ['core'])
        if self.options.debugreport:
            add_component('qa', library_pattern('qa'), ['core', 'xml'])
        if self.options.ribbon:
            add_component('ribbon', library_pattern('ribbon'), ['core'])
        if self.options.richtext:
            add_component('richtext', library_pattern('richtext'), ['core', 'html', 'xml'])
        if self.options.stc:
            add_component('stc', library_pattern('stc'), ['core'])

            if not self.options.shared:
                scintilla_suffix = '{debug}' if self.settings.os == "Windows" else '{suffix}'
                self.cpp_info.components['stc'].libs.append('wxscintilla' + scintilla_suffix.format(debug=debug, suffix=suffix))

        if self.options.webview:
            add_component('webview', library_pattern('webview'), ['core'])
        if self.options.xrc:
            add_component('xrc', library_pattern('xrc'), ['core', 'html', 'xml'])

        if self.settings.os == 'Macos':
            self.cpp_info.components['base'].frameworks.extend([
                'Carbon', 'Cocoa', 'AudioToolbox', 'OpenGL', 'AVKit', 'AVFoundation',
                'Foundation', 'IOKit', 'ApplicationServices', 'CoreText', 'CoreGraphics',
                'CoreServices', 'CoreMedia', 'Security', 'ImageIO', 'System',])

            if self.options.webview:
                 self.cpp_info.components['base'].frameworks.append('WebKit')
        elif self.settings.os == 'Windows':
            self.cpp_info.components['base'].system_libs.extend([
                'kernel32', 'user32', 'gdi32', 'comdlg32', 'winspool', 'shell32', 'comctl32',
                'ole32', 'oleaut32', 'uuid', 'wininet', 'rpcrt4', 'winmm', 'advapi32', 'wsock32',])
            # Link a few libraries that are needed when using gcc on windows
            if self.settings.compiler == 'gcc':
                self.cpp_info.components['base'].system_libs.extend([
                    'uxtheme', 'version', 'shlwapi', 'oleacc'])
        else:
            self.add_libraries_from_pc('gtk+-2.0', self.cpp_info.components['base'])
            self.add_libraries_from_pc('x11', self.cpp_info.components['base'])
            self.cpp_info.components['base'].system_libs.extend(['dl', 'pthread', 'SM', 'uuid'])
