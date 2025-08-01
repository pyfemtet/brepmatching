pybind11_add_module(automate_cpp
	${CMAKE_CURRENT_SOURCE_DIR}/cpp/automate.cpp
	${CMAKE_CURRENT_SOURCE_DIR}/cpp/disjointset.h
	${CMAKE_CURRENT_SOURCE_DIR}/cpp/disjointset.cpp 
	${CMAKE_CURRENT_SOURCE_DIR}/cpp/lsh.h
	${CMAKE_CURRENT_SOURCE_DIR}/cpp/lsh.cpp 
	${CMAKE_CURRENT_SOURCE_DIR}/cpp/eclass.h
	${CMAKE_CURRENT_SOURCE_DIR}/cpp/eclass.cpp 
	${CMAKE_CURRENT_SOURCE_DIR}/cpp/part.h
	${CMAKE_CURRENT_SOURCE_DIR}/cpp/part.cpp
)

# ビルド時に Eigen の LGPL コードへの依存を外す
target_compile_definitions(automate_cpp PRIVATE "-DEIGEN_MPL2_ONLY")

# ===== Femtet 内の breploader をリンクする =====
# include
target_include_directories(automate_cpp PUBLIC ${FEMTET_LIB_DIR}/breploader/include)

# DLLライブラリへのリンク設定（ビルドしたDLLが存在する場所）
if (DEFINED ENV{BREPLOADER_DIR})
    target_link_libraries(automate_cpp PUBLIC $ENV{BREPLOADER_DIR}/breploader_d.lib)
else()
    target_link_libraries(automate_cpp PUBLIC ${FEMTET_LIB_DIR}/breploader/lib/breploader.lib)
endif()

# Eigen3 へのリンクを追加
target_include_directories(automate_cpp PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
