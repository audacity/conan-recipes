cmake_minimum_required(VERSION 3.1)
project(test_package)

find_package(libid3tag REQUIRED CONFIG)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} libid3tag::libid3tag)
