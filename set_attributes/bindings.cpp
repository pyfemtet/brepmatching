#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <sa_lib.h>
#include <map>
#include <string>
#include <tuple>

PYBIND11_MODULE(set_attributes, m) {
    m.def("set_attributes_to_xt", &set_attributes_to_xt);
}