cmake_minimum_required(VERSION 3.14)
project(brepmatching_dependencies)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON) # 全てのシンボルをエクスポート
# set(CMAKE_BUILD_TYPE Debug) # デバッグビルド

# ===== FEMTET_ROOT_DIR の決定 =====

# set(<variable> <value> [...] CACHE <type> <docstring> [FORCE])
set(FEMTET_ROOT_DIR "" CACHE PATH "Femtet root directory")

# 1. 環境変数からの取得を優先
if (FEMTET_ROOT_DIR STREQUAL "")
    if(DEFINED ENV{FEMTET_ROOT_DIR})
        set(FEMTET_ROOT_DIR "$ENV{FEMTET_ROOT_DIR}")
        message(STATUS "Using `FEMTET_ROOT_DIR` environment variable: ${FEMTET_ROOT_DIR}")
    endif()
endif()

# 2. 環境変数にない場合 レジストリから取得
if (FEMTET_ROOT_DIR STREQUAL "")
    if (WIN32)
        # 64bit FemtetMacro.dll 
        # 32 bit 対応する場合は Macro32 フォルダを外すこと
        execute_process(
        COMMAND reg query "HKLM\\SOFTWARE\\Classes\\TypeLib\\{7D1A10D9-22CE-4EDE-80FB-26A1E307D9FA}\\1.0\\0\\win64" /ve
        OUTPUT_VARIABLE FEMTETMACRO_REG_RESULT
        ERROR_QUIET
        OUTPUT_STRIP_TRAILING_WHITESPACE
        )
        if (FEMTETMACRO_REG_RESULT)
            string(REGEX REPLACE ".*REG_SZ[ \t]*" "" FEMTETMACRO_DLL_PATH "${FEMTETMACRO_REG_RESULT}")
            # femtetmacro.dllはFEMTET_ROOT_DIR直下にある
            get_filename_component(FEMTET_ROOT_DIR "${FEMTETMACRO_DLL_PATH}" DIRECTORY)
            message(STATUS "Constructing `FEMTET_ROOT_DIR` from registory: ${FEMTET_ROOT_DIR}")
        endif()
    endif()
endif()

# 3. 見つからなければエラー
if(FEMTET_ROOT_DIR STREQUAL "")
    message(FATAL_ERROR "Femtet root directory could not be determined! (Registry and FEMTET_ROOT_DIR env not found)")
endif()

# 4. FEMTET_LIB_DIR と femtetmacro.dll のパスを設定
set(FEMTET_LIB_DIR "${FEMTET_ROOT_DIR}/lib")
set(FEMTETMACRO_DLL_PATH "${FEMTET_ROOT_DIR}/femtetmacro.dll")

# 確認メッセージ
message(STATUS "FEMTET_ROOT_DIR: ${FEMTET_ROOT_DIR}")
message(STATUS "FEMTET_LIB_DIR: ${FEMTET_LIB_DIR}")
message(STATUS "FEMTETMACRO_DLL_PATH: ${FEMTETMACRO_DLL_PATH}")


# ===== Add subdirectories =====
find_package(pybind11 CONFIG REQUIRED)

add_subdirectory("src/set_attributes")
add_subdirectory("src/coincidence_matching")
add_subdirectory("src/automate")
