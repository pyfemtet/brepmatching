# ===== coincidence_matching =====
# coincidence_matching
pybind11_add_module(coincidence_matching ${CMAKE_CURRENT_LIST_DIR}/bindings.cpp)


# ===== cm_lib on Femtet =====
# DLLのインクルードディレクトリを指定
target_include_directories(coincidence_matching PUBLIC ${FEMTET_LIB_DIR}/cm_lib/include)

# DLLライブラリへのリンク設定（ビルドしたDLLが存在する場所）

if (DEFINED ENV{CM_LIB_DIR})
    target_link_libraries(coincidence_matching PUBLIC $ENV{CM_LIB_DIR}/cm_lib_d.lib)
else()
    target_link_libraries(coincidence_matching PUBLIC ${FEMTET_LIB_DIR}/cm_lib/lib/cm_lib.lib)
endif()
