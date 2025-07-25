from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os, fix_apple_shared_install_name
from conan.tools.build import cross_building
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.env import VirtualBuildEnv, VirtualRunEnv
from conan.tools.files import copy, download, get, load, replace_in_file, rm, rmdir, save
from conan.tools.gnu import Autotools, AutotoolsToolchain, AutotoolsDeps, PkgConfigDeps
from conan.tools.layout import basic_layout
from conan.tools.microsoft import is_msvc, unix_path
from conan.tools.scm import Version

import os
import re

required_conan_version = ">=2.1.0"


class LibcurlConan(ConanFile):
    name = "libcurl"
    description = "command line tool and library for transferring data with URLs"
    license = "curl"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://curl.se"
    topics = ("curl", "data-transfer",
            "ftp", "gopher", "http", "imap", "ldap", "mqtt", "pop3", "rtmp", "rtsp",
            "scp", "sftp", "smb", "smtp", "telnet", "tftp")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_executable": [True, False],
        "with_ssl": [False, "openssl", "wolfssl", "schannel", "darwinssl", "mbedtls", "libressl"],
        "with_file": [True, False],
        "with_ftp": [True, False],
        "with_http": [True, False],
        "with_ldap": [True, False],
        "with_rtsp": [True, False],
        "with_dict": [True, False],
        "with_telnet": [True, False],
        "with_tftp": [True, False],
        "with_pop3": [True, False],
        "with_imap": [True, False],
        "with_smb": [True, False],
        "with_smtp": [True, False],
        "with_gopher": [True, False],
        "with_mqtt": [True, False],
        "with_libssh2": [True, False],
        "with_libidn": [True, False],
        "with_librtmp": [True, False],
        "with_libgsasl": [True, False],
        "with_libpsl": [True, False],
        "with_largemaxwritesize": [True, False],
        "with_nghttp2": [True, False],
        "with_zlib": [True, False],
        "with_brotli": [True, False],
        "with_zstd": [True, False],
        "with_c_ares": [True, False],
        "with_threaded_resolver": [True, False],
        "with_proxy": [True, False],
        "with_crypto_auth": [True, False],
        "with_ntlm": [True, False],
        "with_ntlm_wb": [True, False],
        "with_cookies": [True, False],
        "with_ipv6": [True, False],
        "with_docs": [True, False],
        "with_misc_docs": [True, False],
        "with_verbose_debug": [True, False],
        "with_symbol_hiding": [True, False],
        "with_unix_sockets": [True, False],
        "with_verbose_strings": [True, False],
        "with_ca_bundle": [False, "auto", "ANY"],
        "with_ca_path": [False, "auto", "ANY"],
        "with_ca_fallback": [True, False],
        "with_form_api": [True, False],
        "with_websockets": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_executable": False,
        "with_ssl": "openssl",
        "with_dict": True,
        "with_file": True,
        "with_ftp": True,
        "with_gopher": True,
        "with_http": True,
        "with_imap": True,
        "with_ldap": False,
        "with_mqtt": True,
        "with_pop3": True,
        "with_rtsp": True,
        "with_smb": True,
        "with_smtp": True,
        "with_telnet": True,
        "with_tftp": True,
        "with_libssh2": False,
        "with_libidn": False,
        "with_librtmp": False,
        "with_libgsasl": False,
        "with_libpsl": False,
        "with_largemaxwritesize": False,
        "with_nghttp2": False,
        "with_zlib": True,
        "with_brotli": False,
        "with_zstd": False,
        "with_c_ares": False,
        "with_threaded_resolver": True,
        "with_proxy": True,
        "with_crypto_auth": True,
        "with_ntlm": True,
        "with_ntlm_wb": True,
        "with_cookies": True,
        "with_ipv6": True,
        "with_docs": False,
        "with_misc_docs": False,
        "with_verbose_debug": True,
        "with_symbol_hiding": False,
        "with_unix_sockets": True,
        "with_verbose_strings": True,
        "with_ca_bundle": "auto",
        "with_ca_path": "auto",
        "with_ca_fallback": False,
        "with_form_api": True,
        "with_websockets": True,
    }

    @property
    def _is_mingw(self):
        return self.settings.os == "Windows" and self.settings.compiler == "gcc"

    @property
    def _is_win_x_android(self):
        return self.settings.os == "Android" and self.settings_build.os == "Windows"

    @property
    def _is_using_cmake_build(self):
        return is_msvc(self) or self._is_win_x_android

    def export_sources(self):
        copy(self, "lib_Makefile_add.am", self.recipe_folder, self.export_sources_folder)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC
        if self._is_using_cmake_build:
            del self.options.with_libgsasl

        if Version(self.version) < "8.3.0":
            del self.options.with_form_api
        if Version(self.version) < "8.7.0":
            del self.options.with_misc_docs
        if Version(self.version) < "8.11.0":
            del self.options.with_websockets

        # Default options
        self.options.with_ssl = "darwinssl" if is_apple_os(self) else "openssl"

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.libcxx")
        self.settings.rm_safe("compiler.cppstd")

    def layout(self):
        if self._is_using_cmake_build:
            cmake_layout(self, src_folder="src")
        else:
            basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_ssl == "openssl":
            self.requires("openssl/[>=1.1 <4]@audacity/stable")
        elif self.options.with_ssl == "libressl":
            self.requires("libressl/[>=3.5 <4]")
        elif self.options.with_ssl == "wolfssl":
            self.requires("wolfssl/5.6.6")
        elif self.options.with_ssl == "mbedtls":
            self.requires("mbedtls/3.5.0")
        if self.options.with_nghttp2:
            self.requires("libnghttp2/1.59.0")
        if self.options.with_libssh2:
            self.requires("libssh2/1.11.0")
        if self.options.with_zlib:
            self.requires("zlib/[>=1.2.13 <1.4]@audacity/stable")
        if self.options.with_brotli:
            self.requires("brotli/1.0.9@audacity/stable")
        if self.options.with_zstd:
            self.requires("zstd/1.5.5@audacity/stable")
        if self.options.with_c_ares:
            self.requires("c-ares/[>=1.27 <2]")
        if self.options.get_safe("with_libpsl"):
            self.requires("libpsl/0.21.1")
        if self.options.with_libidn:
            self.requires("libidn2/2.3.0")


    def validate(self):
        if self.options.with_ssl == "schannel" and self.settings.os != "Windows":
            raise ConanInvalidConfiguration("schannel only suppported on Windows.")
        if self.options.with_ssl == "darwinssl" and not is_apple_os(self):
            raise ConanInvalidConfiguration("darwinssl only suppported on Apple like OS (Macos, iOS, watchOS or tvOS).")
        if self.options.with_ssl == "openssl":
            openssl = self.dependencies["openssl"]
            if self.options.with_ntlm and openssl.options.no_des:
                raise ConanInvalidConfiguration("option with_ntlm=True requires openssl/*:no_des=False")
        if self.options.with_ssl == "wolfssl" and not self.dependencies["wolfssl"].options.with_curl:
            raise ConanInvalidConfiguration("option with_ssl=wolfssl requires wolfssl/*:with_curl=True")

    def build_requirements(self):
        if self._is_using_cmake_build:
            if self._is_win_x_android:
                self.tool_requires("ninja/1.11.0@audacity/stable")
        else:
            self.tool_requires("libtool/2.4.7@audacity/stable")
            if not self.conf.get("tools.gnu:pkg_config", check_type=str):
                self.tool_requires("pkgconf/1.9.3@audacity/stable")
            if self.settings.os in [ "tvOS", "watchOS" ]:
                self.tool_requires("gnu-config/cci.20210814@audacity/stable")
            if self.settings_build.os == "Windows":
                self.win_bash = True
                if not self.conf.get("tools.microsoft.bash:path", check_type=str):
                    self.tool_requires("msys2/cci.latest")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        cert_url = self.conf.get("user.libcurl.cert:url", check_type=str) or "https://curl.se/ca/cacert-2023-08-22.pem"
        cert_sha256 = self.conf.get("user.libcurl.cert:sha256", check_type=str) or "23c2469e2a568362a62eecf1b49ed90a15621e6fa30e29947ded3436422de9b9"
        download(self, cert_url, "cacert.pem", verify=True, sha256=cert_sha256)

    def generate(self):
        env = VirtualBuildEnv(self)
        env.generate()
        if self._is_using_cmake_build:
            self._generate_with_cmake()
        else:
            self._generate_with_autotools()

    def build(self):
        self._patch_sources()
        if self._is_using_cmake_build:
            cmake = CMake(self)
            cmake.configure()
            cmake.build()
        else:
            autotools = Autotools(self)
            autotools.autoreconf()
            # autoreconf is caalled with "--force" which regenerate all files.
            # Because we want to use a patched config.sub for tvOS/watchOS, we
            # need to call this patch after autoreconf.
            self._patch_autoreconf()
            autotools.configure()
            autotools.make()

    def _patch_autoreconf(self):
        # Fix config.sub for tvOS/watchOS
        if self.settings.os in [ "tvOS", "watchOS" ]:
            for gnu_config in [
                    self.conf.get("user.gnu-config:config_guess", check_type=str),
                    self.conf.get("user.gnu-config:config_sub", check_type=str),
            ]:
                if gnu_config:
                    copy(self, os.path.basename(gnu_config), src=os.path.dirname(gnu_config), dst=self.source_folder)

    def _patch_sources(self):
        self._patch_misc_files()
        self._patch_autotools()
        self._patch_cmake()

    def _patch_misc_files(self):
        if self.options.with_largemaxwritesize:
            replace_in_file(self, os.path.join(self.source_folder, "include", "curl", "curl.h"),
                                  "define CURL_MAX_WRITE_SIZE 16384",
                                  "define CURL_MAX_WRITE_SIZE 10485760")

        # https://github.com/curl/curl/issues/2835
        # for additional info, see this comment https://github.com/conan-io/conan-center-index/pull/1008#discussion_r386122685
        if self.settings.compiler == "apple-clang" and self.settings.compiler.version == "9.1":
            if self.options.with_ssl == "darwinssl":
                replace_in_file(self, os.path.join(self.source_folder, "lib", "vtls", "sectransp.c"),
                                      "#define CURL_BUILD_MAC_10_13 MAC_OS_X_VERSION_MAX_ALLOWED >= 101300",
                                      "#define CURL_BUILD_MAC_10_13 0")

    def _patch_autotools(self):
        if self._is_using_cmake_build:
            return

        # Disable the executable build if requested
        top_makefile = os.path.join(self.source_folder, "Makefile.am")
        if Version(self.version) < "8.8.0" and not self.options.build_executable:
            replace_in_file(self, top_makefile, "SUBDIRS = lib src", "SUBDIRS = lib")
        elif Version(self.version) >= "8.8.0" and not self.options.build_executable:
            replace_in_file(self, top_makefile, "SUBDIRS = lib docs src scripts", "SUBDIRS = lib")
        elif Version(self.version) >= "8.8.0" and self.options.build_executable:
            replace_in_file(self, top_makefile, "SUBDIRS = lib docs src scripts", "SUBDIRS = lib src")

        # `Makefile.inc` has been removed from 8.12.0 onwards
        if Version(self.version) < "8.12.0":
            replace_in_file(self, top_makefile, "include src/Makefile.inc", "")

        # zlib naming is not always very consistent
        if self.options.with_zlib:
            configure_ac = os.path.join(self.source_folder, "configure.ac")
            zlib_name = self.dependencies["zlib"].cpp_info.aggregated_components().libs[0]
            replace_in_file(self, configure_ac,
                                  "AC_CHECK_LIB(z,",
                                  f"AC_CHECK_LIB({zlib_name},")
            replace_in_file(self, configure_ac,
                                  "-lz",
                                  f"-l{zlib_name} ")

        if self._is_mingw and self.options.shared:
            # patch for shared mingw build
            lib_makefile = os.path.join(self.source_folder, "lib", "Makefile.am")
            replace_in_file(self, lib_makefile,
                                  "noinst_LTLIBRARIES = libcurlu.la",
                                  "")
            replace_in_file(self, lib_makefile,
                                  "noinst_LTLIBRARIES =",
                                  "")
            replace_in_file(self, lib_makefile,
                                  "lib_LTLIBRARIES = libcurl.la",
                                  "noinst_LTLIBRARIES = libcurl.la")

            if self.options.build_executable:
                # Link libcurl.dll.a to curl.exe
                replace_in_file(self, os.path.join(self.source_folder, "src", "Makefile.am"),
                                        "curl_LDADD = $(top_builddir)/lib/libcurl.la",
                                        "curl_LDADD = $(top_builddir)/lib/libcurl.la $(top_builddir)/lib/libcurl.dll.a")
            # add directives to build dll
            # used only for native mingw-make
            if not cross_building(self) or self._is_mingw:
                # The patch file is located in the base src folder
                added_content = load(self, os.path.join(self.folders.base_source, "lib_Makefile_add.am"))
                save(self, lib_makefile, added_content, append=True)

    def _patch_cmake(self):
        if not self._is_using_cmake_build:
            return
        cmakelists = os.path.join(self.source_folder, "CMakeLists.txt")
        # TODO: check this patch, it's suspicious
        if Version(self.version) < "8.4.0":
            replace_in_file(self, cmakelists,
                                "include(CurlSymbolHiding)", "")

        if Version(self.version) >= "8.12.0":
            cmakemacros = os.path.join(self.source_folder, "CMake", "Macros.cmake")
            replace_in_file(self, cmakemacros, "macro(curl_dependency_option _option_name _find_name _desc_name)", "macro(curl_dependency_option _option_name _find_name _desc_name _cmake_args)")
            replace_in_file(self, cmakemacros, "find_package(${_find_name} REQUIRED)", "find_package(${_find_name} ${_cmake_args})")

        # brotli
        if Version(self.version) < "8.2.0":
            replace_in_file(self, cmakelists, "find_package(Brotli QUIET)", "find_package(brotli REQUIRED CONFIG)")
        else:
            if Version(self.version) < "8.12.0":
                replace_in_file(self, cmakelists, "find_package(Brotli REQUIRED)", "find_package(brotli REQUIRED CONFIG)")
            else:
                replace_in_file(self, cmakelists, 'curl_dependency_option(CURL_BROTLI Brotli "brotli")', 'curl_dependency_option(CURL_BROTLI brotli "brotli" "REQUIRED CONFIG")')
        replace_in_file(self, cmakelists, "if(BROTLI_FOUND)", "if(brotli_FOUND)")
        replace_in_file(self, cmakelists, "${BROTLI_LIBRARIES}", "brotli::brotli")
        replace_in_file(self, cmakelists, "${BROTLI_INCLUDE_DIRS}", "${brotli_INCLUDE_DIRS}")

        # zstd
        # Use upstream FindZstd.cmake because check_symbol_exists() is called
        # afterwards and it would fail with zstd_LIBRARIES generated by CMakeDeps
        if Version(self.version) < "8.12.0":
            replace_in_file(self, cmakelists, "find_package(Zstd REQUIRED)", "find_package(Zstd REQUIRED MODULE)")
        else:
            replace_in_file(self, cmakelists, 'curl_dependency_option(CURL_ZSTD Zstd "zstd")', 'curl_dependency_option(CURL_ZSTD Zstd "zstd" "REQUIRED MODULE")')
        if Version(self.version) < "8.10.0":
            replace_in_file(self, os.path.join(self.source_folder, "CMake", "FindZstd.cmake"), "if(UNIX)", "if(0)")

        # zlib
        if Version(self.version) >= "8.12.0":
            replace_in_file(self, cmakelists, 'curl_dependency_option(CURL_ZLIB ZLIB "ZLIB")', 'curl_dependency_option(CURL_ZLIB ZLIB "ZLIB" "")')

        # c-ares
        if Version(self.version) < "8.10.0":
            replace_in_file(self, cmakelists, "find_package(CARES REQUIRED)", "find_package(c-ares REQUIRED CONFIG)")
            replace_in_file(self, cmakelists, "${CARES_LIBRARY}", "c-ares::cares")
        else:
            replace_in_file(self, cmakelists, "find_package(Cares REQUIRED)", "find_package(c-ares REQUIRED CONFIG)")
            replace_in_file(self, cmakelists, "${CARES_LIBRARIES}", "c-ares::cares")

        # libpsl
        if Version(self.version) < "8.10.0":
            replace_in_file(self, cmakelists, "find_package(LibPSL)", "find_package(libpsl REQUIRED CONFIG)")
            replace_in_file(self, cmakelists, "${LIBPSL_LIBRARY}", "libpsl::libpsl")
            replace_in_file(self, cmakelists, "${LIBPSL_INCLUDE_DIR}", "${libpsl_INCLUDE_DIRS}")
        else:
            replace_in_file(self, cmakelists, "${LIBPSL_LIBRARIES}", "libpsl::libpsl")
            replace_in_file(self, cmakelists, "${LIBPSL_INCLUDE_DIRS}", "${libpsl_INCLUDE_DIRS}")
        if Version(self.version) < "8.12.0":
            replace_in_file(self, cmakelists, "if(LIBPSL_FOUND)", "if(libpsl_FOUND)")

        # libssh2
        if Version(self.version) < "8.10.0":
            replace_in_file(self, cmakelists, "find_package(LibSSH2)", "find_package(Libssh2 REQUIRED CONFIG)")
            replace_in_file(self, cmakelists, "${LIBSSH2_LIBRARY}", "Libssh2::libssh2")
            replace_in_file(self, cmakelists, "${LIBSSH2_INCLUDE_DIR}", "${Libssh2_INCLUDE_DIRS}")
        else:
            replace_in_file(self, cmakelists, "${LIBSSH2_LIBRARIES}", "Libssh2::libssh2")
            replace_in_file(self, cmakelists, "${LIBSSH2_INCLUDE_DIRS}", "${Libssh2_INCLUDE_DIRS}")
        replace_in_file(self, cmakelists, "if(LIBSSH2_FOUND)", "if(Libssh2_FOUND)")

        # libnghttp2
        if Version(self.version) < "8.10.0":
            replace_in_file(self, cmakelists, "find_package(NGHTTP2 REQUIRED)", "find_package(libnghttp2 REQUIRED CONFIG)")
        else:
            replace_in_file(self, cmakelists, "find_package(NGHTTP2)", "find_package(libnghttp2 REQUIRED CONFIG)")
            replace_in_file(self, cmakelists, "NGHTTP2_FOUND", "libnghttp2_FOUND")
        replace_in_file(self, cmakelists, "${NGHTTP2_INCLUDE_DIRS}", "${libnghttp2_INCLUDE_DIRS}")
        replace_in_file(self, cmakelists, "${NGHTTP2_LIBRARIES}", "libnghttp2::nghttp2")

        # wolfssl
        replace_in_file(self, cmakelists, "find_package(WolfSSL REQUIRED)", "find_package(wolfssl REQUIRED CONFIG)")
        if Version(self.version) < "8.10.0":
            replace_in_file(self, cmakelists, "${WolfSSL_LIBRARIES}", "${wolfssl_LIBRARIES}")
            replace_in_file(self, cmakelists, "${WolfSSL_INCLUDE_DIRS}", "${wolfssl_INCLUDE_DIRS}")
        else:
            replace_in_file(self, cmakelists, "${WOLFSSL_LIBRARIES}", "${wolfssl_LIBRARIES}")
            replace_in_file(self, cmakelists, "${WOLFSSL_INCLUDE_DIRS}", "${wolfssl_INCLUDE_DIRS}")


        # INTERFACE_LIBRARY (generated by the cmake_find_package generator) targets doesn't have the LOCATION property.
        # So skipp the LOCATION check in the CMakeLists.txt
        replace_in_file(
            self,
            cmakelists,
            'get_target_property(_lib "${_libname}" LOCATION)',
            """get_target_property(_type "${_libname}" TYPE)
    if(${_type} STREQUAL "INTERFACE_LIBRARY")
      # Reading the INTERFACE_LIBRARY property on non-imported target will error out.
      continue()
    endif()
    get_target_property(_lib "${_libname}" LOCATION)""",
        )

    def _yes_no(self, value):
        return "yes" if value else "no"

    def _generate_with_autotools(self):
        if not cross_building(self):
            env = VirtualRunEnv(self)
            env.generate(scope="build")

        tc = AutotoolsToolchain(self)
        tc.configure_args.extend([
            f"--with-libidn2={self._yes_no(self.options.with_libidn)}",
            f"--with-librtmp={self._yes_no(self.options.with_librtmp)}",
            f"--with-libpsl={self._yes_no(self.options.with_libpsl)}",
            f"--with-libgsasl={self._yes_no(self.options.with_libgsasl)}",
            f"--with-schannel={self._yes_no(self.options.with_ssl == 'schannel')}",
            f"--with-secure-transport={self._yes_no(self.options.with_ssl == 'darwinssl')}",
            f"--with-brotli={self._yes_no(self.options.with_brotli)}",
            f"--enable-shared={self._yes_no(self.options.shared)}",
            f"--enable-static={self._yes_no(not self.options.shared)}",
            f"--enable-dict={self._yes_no(self.options.with_dict)}",
            f"--enable-file={self._yes_no(self.options.with_file)}",
            f"--enable-ftp={self._yes_no(self.options.with_ftp)}",
            f"--enable-gopher={self._yes_no(self.options.with_gopher)}",
            f"--enable-http={self._yes_no(self.options.with_http)}",
            f"--enable-imap={self._yes_no(self.options.with_imap)}",
            f"--enable-ldap={self._yes_no(self.options.with_ldap)}",
            f"--enable-mqtt={self._yes_no(self.options.with_mqtt)}",
            f"--enable-pop3={self._yes_no(self.options.with_pop3)}",
            f"--enable-rtsp={self._yes_no(self.options.with_rtsp)}",
            f"--enable-smb={self._yes_no(self.options.with_smb)}",
            f"--enable-smtp={self._yes_no(self.options.with_smtp)}",
            f"--enable-telnet={self._yes_no(self.options.with_telnet)}",
            f"--enable-tftp={self._yes_no(self.options.with_tftp)}",
            f"--enable-debug={self._yes_no(self.settings.build_type == 'Debug')}",
            f"--enable-ares={self._yes_no(self.options.with_c_ares)}",
            f"--enable-threaded-resolver={self._yes_no(self.options.with_threaded_resolver)}",
            f"--enable-cookies={self._yes_no(self.options.with_cookies)}",
            f"--enable-ipv6={self._yes_no(self.options.with_ipv6)}",
            f"--enable-manual={self._yes_no(self.options.with_docs)}",
            f"--enable-verbose={self._yes_no(self.options.with_verbose_debug)}",
            f"--enable-symbol-hiding={self._yes_no(self.options.with_symbol_hiding)}",
            f"--enable-unix-sockets={self._yes_no(self.options.get_safe('with_unix_sockets'))}",
            f"--with-zstd={self._yes_no(self.options.with_zstd)}",
        ])

        # Since 7.77.0, disabling TLS must be explicitly requested otherwise it fails
        if not self.options.with_ssl:
            tc.configure_args.append("--without-ssl")

        if self.options.with_ssl == "openssl":
            path = unix_path(self, self.dependencies["openssl"].package_folder)
            tc.configure_args.append(f"--with-openssl={path}")
        elif self.options.with_ssl == "libressl":
            path = unix_path(self, self.dependencies["libressl"].package_folder)
            tc.configure_args.append(f"--with-openssl={path}")
        else:
            tc.configure_args.append("--without-openssl")

        if self.options.with_ssl == "wolfssl":
            path = unix_path(self, self.dependencies["wolfssl"].package_folder)
            tc.configure_args.append(f"--with-wolfssl={path}")
        else:
            tc.configure_args.append("--without-wolfssl")

        if self.options.with_ssl == "mbedtls":
            path = unix_path(self, self.dependencies["mbedtls"].package_folder)
            tc.configure_args.append(f"--with-mbedtls={path}")
        else:
            tc.configure_args.append("--without-mbedtls")

        if self.options.with_libssh2:
            path = unix_path(self, self.dependencies["libssh2"].package_folder)
            tc.configure_args.append(f"--with-libssh2={path}")
        else:
            tc.configure_args.append("--without-libssh2")

        if self.options.with_nghttp2:
            path = unix_path(self, self.dependencies["libnghttp2"].package_folder)
            tc.configure_args.append(f"--with-nghttp2={path}")
        else:
            tc.configure_args.append("--without-nghttp2")

        if self.options.with_zlib:
            path = unix_path(self, self.dependencies["zlib"].package_folder)
            tc.configure_args.append(f"--with-zlib={path}")
        else:
            tc.configure_args.append("--without-zlib")

        if not self.options.with_proxy:
            tc.configure_args.append("--disable-proxy")

        if not self.options.with_rtsp:
            tc.configure_args.append("--disable-rtsp")

        if not self.options.with_crypto_auth:
            tc.configure_args.append("--disable-crypto-auth") # also disables NTLM in versions of curl prior to 7.78.0

        # ntlm will default to enabled if any SSL options are enabled
        if not self.options.with_ntlm:
            tc.configure_args.append("--disable-ntlm")

        if not self.options.with_ntlm_wb:
            tc.configure_args.append("--disable-ntlm-wb")

        if not self.options.with_ca_bundle:
            tc.configure_args.append("--without-ca-bundle")
        elif self.options.with_ca_bundle != "auto":
            tc.configure_args.append(f"--with-ca-bundle={str(self.options.with_ca_bundle)}")

        if not self.options.with_ca_path:
            tc.configure_args.append("--without-ca-path")
        elif self.options.with_ca_path != "auto":
            tc.configure_args.append(f"--with-ca-path={str(self.options.with_ca_path)}")

        tc.configure_args.append(f"--with-ca-fallback={self._yes_no(self.options.with_ca_fallback)}")

        if "with_misc_docs" in self.options:
            if self.options.with_misc_docs:
                tc.configure_args.append("--enable-docs")
            else:
                tc.configure_args.append("--disable-docs")
        if "with_form_api" in self.options:
            if self.options.with_form_api:
                tc.configure_args.append("--enable-form-api")
            else:
                tc.configure_args.append("--disable-form-api")
        if "with_websockets" in self.options:
            if self.options.with_websockets:
                tc.configure_args.append("--enable-websockets")
            else:
                tc.configure_args.append("--disable-websockets")

        if self.options.with_libidn:
            path = unix_path(self, self.dependencies["libidn2"].package_folder)
            tc.configure_args.append(f"--with-libidn2={path}")
        else:
            tc.configure_args.append("--without-libidn2")

        # Cross building flags
        if cross_building(self):
            if self.settings.os == "Linux" and "arm" in self.settings.arch:
                tc.configure_args.append(f"--host={self._get_linux_arm_host()}")
            elif is_apple_os(self) and not self.settings.os == "Macos":
                tc.configure_args.append("--enable-threaded-resolver")
                tc.configure_args.append("--disable-verbose")
                if self.options.build_executable:
                    # INFO: Need to propage required frameworks to the executable build. Otherwise it will fail to link.
                    tc.extra_ldflags.extend(["-Wl,-framework,CoreFoundation", "-Wl,-framework,Security"])
            elif self.settings.os == "Android":
                pass # this just works, conan is great!

        env = tc.environment()

        # tweaks for mingw
        if self._is_mingw:
            rcflags = "-O COFF"
            if self.settings.arch == "x86":
                rcflags += " --target=pe-i386"
            elif self.settings.arch == "x86_64":
                rcflags += " --target=pe-x86-64"
                tc.extra_defines.append("_AMD64_")
            env.define("RCFLAGS", rcflags)

        if self.settings.os != "Windows":
            tc.fpic = self.options.get_safe("fPIC", True)

        if cross_building(self) and is_apple_os(self):
            tc.extra_defines.extend(['HAVE_SOCKET', 'HAVE_FCNTL_O_NONBLOCK'])

        tc.generate(env)
        tc = PkgConfigDeps(self)
        tc.generate()
        tc = AutotoolsDeps(self)
        tc.generate()

    def _get_linux_arm_host(self):
        arch = None
        if self.settings.os == "Linux":
            arch = "arm-linux-gnu"
            # aarch64 could be added by user
            if "aarch64" in self.settings.arch:
                arch = "aarch64-linux-gnu"
            elif "arm" in self.settings.arch and "hf" in self.settings.arch:
                arch = "arm-linux-gnueabihf"
            elif "arm" in self.settings.arch and self._arm_version(str(self.settings.arch)) > 4:
                arch = "arm-linux-gnueabi"
        return arch

    # TODO, this should be a inner fuction of _get_linux_arm_host since it is only used from there
    # it should not polute the class namespace, since there are iOS and Android arm aritectures also
    def _arm_version(self, arch):
        version = None
        match = re.match(r"arm\w*(\d)", arch)
        if match:
            version = int(match.group(1))
        return version

    def _generate_with_cmake(self):
        if self._is_win_x_android:
            tc = CMakeToolchain(self, generator="Ninja")
        else:
            tc = CMakeToolchain(self)
        tc.variables["ENABLE_UNICODE"] = True
        tc.variables["BUILD_TESTING"] = False
        tc.variables["BUILD_CURL_EXE"] = self.options.build_executable
        tc.cache_variables["ENABLE_CURL_MANUAL"] = False
        tc.variables["CURL_DISABLE_LDAP"] = not self.options.with_ldap
        tc.variables["BUILD_SHARED_LIBS"] = self.options.shared
        tc.variables["CURL_STATICLIB"] = not self.options.shared
        tc.variables["CMAKE_DEBUG_POSTFIX"] = ""
        tc.variables["CURL_USE_SCHANNEL"] = self.options.with_ssl == "schannel"
        tc.variables["CURL_USE_OPENSSL"] = self.options.with_ssl in ("openssl", "libressl")
        tc.variables["CURL_USE_WOLFSSL"] = self.options.with_ssl == "wolfssl"
        tc.variables["CURL_USE_MBEDTLS"] = self.options.with_ssl == "mbedtls"
        tc.variables["USE_NGHTTP2"] = self.options.with_nghttp2
        tc.variables["CURL_ZLIB"] = self.options.with_zlib
        tc.variables["CURL_BROTLI"] = self.options.with_brotli
        tc.variables["CURL_ZSTD"] = self.options.with_zstd
        tc.variables["CURL_USE_LIBPSL"] = self.options.with_libpsl
        tc.variables["CURL_USE_LIBSSH2"] = self.options.with_libssh2
        tc.variables["ENABLE_ARES"] = self.options.with_c_ares
        if not self.options.with_c_ares:
            tc.variables["ENABLE_THREADED_RESOLVER"] = self.options.with_threaded_resolver
        tc.variables["CURL_DISABLE_PROXY"] = not self.options.with_proxy
        tc.variables["USE_LIBRTMP"] = self.options.with_librtmp
        tc.variables["USE_LIBIDN2"] = self.options.with_libidn
        if self.options.with_libidn:
            # Conan won't generate this variable as we're setting prefixes,
            # and CMake might not either as it's looking for Libidn2
            # Ensure it's there
            tc.cache_variables["LIBIDN2_FOUND"] = True
        tc.variables["CURL_DISABLE_RTSP"] = not self.options.with_rtsp
        tc.variables["CURL_DISABLE_CRYPTO_AUTH"] = not self.options.with_crypto_auth
        tc.variables["CURL_DISABLE_VERBOSE_STRINGS"] = not self.options.with_verbose_strings
        if self.options.with_ssl == "libressl":
            tc.variables["CURL_DISABLE_SRP"] = True
        if "with_form_api" in self.options:
            tc.variables["CURL_DISABLE_FORM_API"] = not self.options.with_form_api
        if "with_websockets" in self.options:
            tc.variables["CURL_DISABLE_WEBSOCKETS"] = not self.options.with_websockets

        # Also disables NTLM_WB if set to false
        if not self.options.with_ntlm:
            tc.variables["CURL_DISABLE_NTLM"] = True
        tc.variables["NTLM_WB_ENABLED"] = self.options.with_ntlm_wb

        if self.options.with_ca_bundle:
            tc.cache_variables["CURL_CA_BUNDLE"] = str(self.options.with_ca_bundle)
        else:
            tc.cache_variables["CURL_CA_BUNDLE"] = "none"

        if self.options.with_ca_path:
            tc.cache_variables["CURL_CA_PATH"] = str(self.options.with_ca_path)
        else:
            tc.cache_variables["CURL_CA_PATH"] = "none"

        tc.cache_variables["CURL_CA_FALLBACK"] = self.options.with_ca_fallback

        # TODO: remove this when https://github.com/conan-io/conan/issues/12180 will be fixed.
        if  Version(self.version) >= "8.3.0":
            tc.variables["HAVE_SSL_SET0_WBIO"] = False
        if  Version(self.version) >= "8.4.0":
            tc.variables["HAVE_OPENSSL_SRP"] = True
            tc.variables["HAVE_SSL_CTX_SET_QUIC_METHOD"] = True

        if is_msvc(self):
            tc.cache_variables["CMAKE_TRY_COMPILE_CONFIGURATION"] = str(self.settings.build_type)

        tc.generate()

        deps = CMakeDeps(self)
        deps.set_property("wolfssl", "cmake_additional_variables_prefixes", ["WolfSSL", "WOLFSSL"])
        deps.set_property("wolfssl", "cmake_file_name", "WolfSSL")

        if self.options.with_libidn:
            deps.set_property("libidn2", "cmake_file_name", "Libidn2")
            deps.set_property("libidn2", "cmake_additional_variables_prefixes", ["LIBIDN2"])
        deps.generate()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        copy(self, "cacert.pem", src=self.source_folder, dst=os.path.join(self.package_folder, "res"))
        if self._is_using_cmake_build:
            cmake = CMake(self)
            cmake.install()
            rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        else:
            autotools = Autotools(self)
            autotools.install()
            rmdir(self, os.path.join(self.package_folder, "share"))
            rm(self, "*.la", os.path.join(self.package_folder, "lib"))
            if self._is_mingw and self.options.shared:
                # Handle only mingw libs
                copy(self, pattern="*.dll", src=self.build_folder, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
                copy(self, pattern="*.dll.a", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
                copy(self, pattern="*.lib", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
            fix_apple_shared_install_name(self)
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "CURL")
        self.cpp_info.set_property("cmake_target_name", "CURL::libcurl")
        self.cpp_info.set_property("cmake_find_mode", "both")
        self.cpp_info.set_property("pkg_config_name", "libcurl")

        self.cpp_info.components["curl"].resdirs = ["res"]
        if is_msvc(self):
            self.cpp_info.components["curl"].libs = ["libcurl_imp"] if self.options.shared else ["libcurl"]
        else:
            self.cpp_info.components["curl"].libs = ["curl"]
            if self.settings.os in ["Linux", "FreeBSD"]:
                if self.options.with_librtmp:
                    self.cpp_info.components["curl"].libs.append("rtmp")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.components["curl"].system_libs = ["rt", "pthread"]
        elif self.settings.os == "Windows":
            # used on Windows for VS build, native and cross mingw build
            self.cpp_info.components["curl"].system_libs = ["ws2_32", "bcrypt"]
            if self.options.with_ldap:
                self.cpp_info.components["curl"].system_libs.append("wldap32")
            if self.options.with_ssl in ("schannel", "libressl"):
                self.cpp_info.components["curl"].system_libs.append("crypt32")
        elif is_apple_os(self):
            self.cpp_info.components["curl"].frameworks.append("CoreFoundation")
            self.cpp_info.components["curl"].frameworks.append("CoreServices")
            self.cpp_info.components["curl"].frameworks.append("SystemConfiguration")
            if self.options.with_ldap:
                self.cpp_info.components["curl"].system_libs.append("ldap")
            if self.options.with_ssl == "darwinssl":
                self.cpp_info.components["curl"].frameworks.append("Security")

        if self._is_mingw:
            # provide pthread for dependent packages
            self.cpp_info.components["curl"].cflags.append("-pthread")
            self.cpp_info.components["curl"].exelinkflags.append("-pthread")
            self.cpp_info.components["curl"].sharedlinkflags.append("-pthread")

        if not self.options.shared:
            self.cpp_info.components["curl"].defines.append("CURL_STATICLIB=1")

        if self.options.with_ssl == "openssl":
            self.cpp_info.components["curl"].requires.append("openssl::openssl")
        if self.options.with_ssl == "libressl":
            self.cpp_info.components["curl"].requires.append("libressl::libressl")
        if self.options.with_ssl == "wolfssl":
            self.cpp_info.components["curl"].requires.append("wolfssl::wolfssl")
        if self.options.with_ssl == "mbedtls":
            self.cpp_info.components["curl"].requires.append("mbedtls::mbedtls")
        if self.options.with_nghttp2:
            self.cpp_info.components["curl"].requires.append("libnghttp2::libnghttp2")
        if self.options.with_libssh2:
            self.cpp_info.components["curl"].requires.append("libssh2::libssh2")
        if self.options.with_zlib:
            self.cpp_info.components["curl"].requires.append("zlib::zlib")
        if self.options.with_brotli:
            self.cpp_info.components["curl"].requires.append("brotli::brotli")
        if self.options.with_zstd:
            self.cpp_info.components["curl"].requires.append("zstd::zstd")
        if self.options.with_c_ares:
            self.cpp_info.components["curl"].requires.append("c-ares::c-ares")
        if self.options.get_safe("with_libpsl"):
            self.cpp_info.components["curl"].requires.append("libpsl::libpsl")
        if self.options.with_libidn:
            self.cpp_info.components["curl"].requires.append("libidn2::libidn2")

        self.cpp_info.components["curl"].set_property("cmake_target_name", "CURL::libcurl")
        self.cpp_info.components["curl"].set_property("pkg_config_name", "libcurl")
