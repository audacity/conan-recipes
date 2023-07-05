cmake_minimum_required(VERSION 3.16)
project(test_package)

find_package(KDDockWidgets-qt6 REQUIRED)

add_executable(${PROJECT_NAME} test_package.cpp)
target_link_libraries(${PROJECT_NAME} KDAB::kddockwidgets)
