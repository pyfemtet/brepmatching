# common
cmake_minimum_required(VERSION 3.14)
project(brepmatching_dependencies)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON) # 全てのシンボルをエクスポート
# set(CMAKE_BUILD_TYPE Debug) # デバッグビルド


find_package(pybind11 CONFIG REQUIRED)

add_subdirectory("set_attributes")
add_subdirectory("coincidence_matching")
add_subdirectory("automate")
