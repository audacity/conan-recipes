cmake_minimum_required(VERSION 3.16)
project(breakpad)

set( CMAKE_CXX_STANDARD 14 )

add_library(breakpad_client STATIC)
add_library(breakpad_processor STATIC)
add_library(breakpad_sender STATIC)

set(SRC_DIR "${CMAKE_SOURCE_DIR}/src")

set(INCLUDES
    PRIVATE
        ${SRC_DIR}
)

if(UNIX)
    #autoconf/conan workaround
    list(APPEND INCLUDES
        PRIVATE
            src
    )
    target_compile_definitions(breakpad_client PRIVATE -DHAVE_CONFIG_H)
endif()


target_include_directories(breakpad_client ${INCLUDES})
target_include_directories(breakpad_processor ${INCLUDES})
target_include_directories(breakpad_sender ${INCLUDES})

target_sources(breakpad_processor
    PRIVATE
        ${SRC_DIR}/processor/basic_code_modules.cc
        ${SRC_DIR}/processor/basic_source_line_resolver.cc
        ${SRC_DIR}/processor/call_stack.cc
        ${SRC_DIR}/processor/cfi_frame_info.cc
        ${SRC_DIR}/processor/convert_old_arm64_context.cc
        ${SRC_DIR}/processor/disassembler_x86.cc
        ${SRC_DIR}/processor/dump_context.cc
        ${SRC_DIR}/processor/dump_object.cc
        ${SRC_DIR}/processor/exploitability.cc
        ${SRC_DIR}/processor/exploitability_linux.cc
        ${SRC_DIR}/processor/exploitability_win.cc
        ${SRC_DIR}/processor/fast_source_line_resolver.cc
        ${SRC_DIR}/processor/logging.cc
        ${SRC_DIR}/processor/microdump_processor.cc
        ${SRC_DIR}/processor/minidump.cc
        ${SRC_DIR}/processor/minidump_processor.cc
        ${SRC_DIR}/processor/module_comparer.cc
        ${SRC_DIR}/processor/module_serializer.cc
        ${SRC_DIR}/processor/pathname_stripper.cc
        ${SRC_DIR}/processor/proc_maps_linux.cc
        ${SRC_DIR}/processor/process_state.cc
        ${SRC_DIR}/processor/simple_symbol_supplier.cc
        ${SRC_DIR}/processor/source_line_resolver_base.cc
        ${SRC_DIR}/processor/stack_frame_cpu.cc
        ${SRC_DIR}/processor/stack_frame_symbolizer.cc
        ${SRC_DIR}/processor/stackwalk_common.cc
        ${SRC_DIR}/processor/stackwalker.cc
        ${SRC_DIR}/processor/stackwalker_address_list.cc
        ${SRC_DIR}/processor/stackwalker_amd64.cc
        ${SRC_DIR}/processor/stackwalker_arm.cc
        ${SRC_DIR}/processor/stackwalker_arm64.cc
        ${SRC_DIR}/processor/stackwalker_mips.cc
        ${SRC_DIR}/processor/stackwalker_ppc.cc
        ${SRC_DIR}/processor/stackwalker_ppc64.cc
        ${SRC_DIR}/processor/stackwalker_selftest.cc
        ${SRC_DIR}/processor/stackwalker_sparc.cc
        ${SRC_DIR}/processor/stackwalker_x86.cc
        ${SRC_DIR}/processor/symbolic_constants_win.cc
        ${SRC_DIR}/processor/synth_minidump.cc
        ${SRC_DIR}/processor/tokenize.cc

        ${SRC_DIR}/third_party/libdisasm/ia32_implicit.c
        ${SRC_DIR}/third_party/libdisasm/ia32_insn.c
        ${SRC_DIR}/third_party/libdisasm/ia32_invariant.c
        ${SRC_DIR}/third_party/libdisasm/ia32_modrm.c
        ${SRC_DIR}/third_party/libdisasm/ia32_opcode_tables.c
        ${SRC_DIR}/third_party/libdisasm/ia32_operand.c
        ${SRC_DIR}/third_party/libdisasm/ia32_reg.c
        ${SRC_DIR}/third_party/libdisasm/ia32_settings.c
        ${SRC_DIR}/third_party/libdisasm/x86_disasm.c
        ${SRC_DIR}/third_party/libdisasm/x86_format.c
        ${SRC_DIR}/third_party/libdisasm/x86_imm.c
        ${SRC_DIR}/third_party/libdisasm/x86_insn.c
        ${SRC_DIR}/third_party/libdisasm/x86_misc.c
        ${SRC_DIR}/third_party/libdisasm/x86_operand_list.c
)

if(APPLE)
    target_sources(breakpad_client
        PRIVATE
            ${SRC_DIR}/client/minidump_file_writer.cc
            ${SRC_DIR}/client/mac/crash_generation/crash_generation_client.cc
            ${SRC_DIR}/client/mac/handler/breakpad_nlist_64.cc
            ${SRC_DIR}/client/mac/handler/dynamic_images.cc
            ${SRC_DIR}/client/mac/handler/exception_handler.cc
            ${SRC_DIR}/client/mac/handler/minidump_generator.cc
            ${SRC_DIR}/client/mac/handler/protected_memory_allocator.cc

            ${SRC_DIR}/common/convert_UTF.cc
            ${SRC_DIR}/common/md5.cc
            ${SRC_DIR}/common/string_conversion.cc
            ${SRC_DIR}/common/mac/bootstrap_compat.cc
            ${SRC_DIR}/common/mac/file_id.cc
            ${SRC_DIR}/common/mac/macho_id.cc
            ${SRC_DIR}/common/mac/macho_utilities.cc
            ${SRC_DIR}/common/mac/macho_walker.cc
            ${SRC_DIR}/common/mac/string_utilities.cc
            ${SRC_DIR}/common/mac/MachIPc.mm
    )
elseif(UNIX)
    target_sources(breakpad_client
        PRIVATE
            ${SRC_DIR}/client/minidump_file_writer.cc
            ${SRC_DIR}/client/linux/crash_generation/crash_generation_client.cc
            ${SRC_DIR}/client/linux/dump_writer_common/thread_info.cc
            ${SRC_DIR}/client/linux/dump_writer_common/ucontext_reader.cc
            ${SRC_DIR}/client/linux/handler/exception_handler.cc
            ${SRC_DIR}/client/linux/handler/minidump_descriptor.cc
            ${SRC_DIR}/client/linux/log/log.cc
            ${SRC_DIR}/client/linux/microdump_writer/microdump_writer.cc
            ${SRC_DIR}/client/linux/minidump_writer/linux_dumper.cc
            ${SRC_DIR}/client/linux/minidump_writer/linux_ptrace_dumper.cc
            ${SRC_DIR}/client/linux/minidump_writer/minidump_writer.cc

            ${SRC_DIR}/common/convert_UTF.cc
            ${SRC_DIR}/common/string_conversion.cc
            ${SRC_DIR}/common/linux/elfutils.cc
            ${SRC_DIR}/common/linux/file_id.cc
            ${SRC_DIR}/common/linux/guid_creator.cc
            ${SRC_DIR}/common/linux/linux_libc_support.cc
            ${SRC_DIR}/common/linux/memory_mapped_file.cc
            ${SRC_DIR}/common/linux/safe_readlink.cc
    )
elseif(WIN32)
    target_sources(breakpad_client
        PRIVATE
            ${SRC_DIR}/client/windows/handler/exception_handler.cc
            ${SRC_DIR}/client/windows/crash_generation/crash_generation_client.cc
            ${SRC_DIR}/common/windows/guid_string.cc
    )
    target_compile_definitions(breakpad_client PRIVATE -DUNICODE)

else()
    message(FATAL_ERROR "Target platform not supported")

endif()

if(UNIX)
    find_package(CURL REQUIRED)
    target_sources(breakpad_sender
        PRIVATE
            ${SRC_DIR}/common/linux/http_upload.cc
    )
    target_link_libraries(breakpad_sender dl ${CURL_LIBRARIES})

elseif(WIN32)
    target_sources(breakpad_sender
        PRIVATE
            ${SRC_DIR}/client/windows/sender/crash_report_sender.cc
            ${SRC_DIR}/common/windows/http_upload.cc
    )
    target_compile_definitions(breakpad_sender PRIVATE -DUNICODE)
    target_link_libraries(breakpad_sender wininet.lib)
endif()
