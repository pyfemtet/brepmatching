# ===== set_attributes =====
# set_attributes モジュールをビルドする宣言
pybind11_add_module(set_attributes ${CMAKE_CURRENT_LIST_DIR}/bindings.cpp)


# ===== Femtet 内の sa_lib をリンクする =====
# DLLのインクルードディレクトリを指定
target_include_directories(set_attributes PUBLIC ${FEMTET_LIB_DIR}/sa_lib/include)

# DLLライブラリへのリンク設定（ビルドしたDLLが存在する場所）
if (DEFINED ENV{SA_LIB_DIR})
    target_link_libraries(set_attributes PUBLIC $ENV{SA_LIB_DIR}/sa_lib_d.lib)
else()
    target_link_libraries(set_attributes PUBLIC ${FEMTET_LIB_DIR}/sa_lib/lib/sa_lib.lib)
endif()
