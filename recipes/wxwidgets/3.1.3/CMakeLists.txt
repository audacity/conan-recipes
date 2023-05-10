cmake_minimum_required(VERSION 2.8.12)
project(cmake_wrapper)

set( CMAKE_CXX_STANDARD 14 )
set( CMAKE_CXX_STANDARD_REQUIRED ON )

include(conanbuildinfo.cmake)
conan_basic_setup()

add_subdirectory("source_subfolder")

if( CMAKE_SYSTEM_NAME MATCHES "Darwin" )
      # When accessibility is enabled, the build will fail in "wx/chkconf.h"
      # since wxRegex compile defines do not include __WXOSX_COCOA__.  So,
      # add it here.
      target_compile_definitions( wxregex PRIVATE "__WXOSX_COCOA__" )
endif()
