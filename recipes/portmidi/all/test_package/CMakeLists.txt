cmake_minimum_required(VERSION 3.10)
project(test_package)

find_package(PortMidi REQUIRED)

add_executable(${PROJECT_NAME} test_package.c)
target_link_libraries(${PROJECT_NAME} portmidi::portmidi)
