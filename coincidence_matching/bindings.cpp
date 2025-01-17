#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <cm_lib.h>
#include <map>
#include <string>
#include <tuple>

namespace py = pybind11;
using namespace pspy;


Matching match_parts(std::string p1, std::string p2, bool exact=false, int int_hWnd=-1) {
	auto matching = make_matching(p1, p2, exact, int_hWnd);
	return matching;
}

std::map<std::string, std::string> match_parts_dict(std::string p1, std::string p2, bool exact = false, int int_hWnd=-1) {
	auto matching = make_matching(p1, p2, exact, int_hWnd);
	std::map<std::string, std::string> matching_dict;
	for (auto matches : { matching.face_matches, matching.edge_matches, matching.vertex_matches }) {
		for (auto match : matches) {
			auto m1 = std::get<0>(match);
			auto m2 = std::get<1>(match);
			matching_dict[m1] = m2;
		}
	}
	if (!exact) {
		for (auto matches : { matching.face_overlaps, matching.edge_overlaps }) {
			for (auto match : matches) {
				auto m1 = std::get<0>(match);
				auto m2 = std::get<1>(match);
				matching_dict[m1] = m2;
			}
		}
	}
	return matching_dict;
}

std::map<std::string, std::string> overlap_parts_dict(std::string p1, std::string p2, int int_hWnd) {
	auto matching = make_matching(p1, p2, false, int_hWnd);
	std::map<std::string, std::string> matching_dict;
	for (auto matches : { matching.face_overlaps, matching.edge_overlaps }) {
		for (auto match : matches) {
			auto m1 = std::get<0>(match);
			auto m2 = std::get<1>(match);
			matching_dict[m1] = m2;
		}
	}
	return matching_dict;
}

std::tuple<std::map<std::string, std::string>, std::map<std::string, std::string> > match_and_overlap_dicts(std::string p1, std::string p2, int int_hWnd) {
	
	auto matching = make_matching(p1, p2, false, int_hWnd);

	std::map<std::string, std::string> matching_dict;
	std::map<std::string, std::string> overlap_dict;

	for (auto matches : { matching.face_matches, matching.edge_matches, matching.vertex_matches }) {
		for (auto match : matches) {
			auto m1 = std::get<0>(match);
			auto m2 = std::get<1>(match);
			matching_dict[m1] = m2;
		}
	}


	for (auto matches : { matching.face_overlaps, matching.edge_overlaps }) {
		for (auto match : matches) {
			auto m1 = std::get<0>(match);
			auto m2 = std::get<1>(match);
			overlap_dict[m1] = m2;
		}
	}

	return std::make_tuple(matching_dict, overlap_dict);
}

PYBIND11_MODULE(coincidence_matching, m) {
	pybind11::class_<Matching>(m, "Matching")
		.def_readwrite("face_matches", &Matching::face_matches)
		.def_readwrite("edge_matches", &Matching::edge_matches)
		.def_readwrite("vertex_matches", &Matching::vertex_matches)
		.def_readwrite("face_overlaps", &Matching::face_overlaps)
		.def_readwrite("edge_overlaps", &Matching::edge_overlaps)
		.def_readwrite("larger_face_overlap_percentages", &Matching::larger_face_overlap_percentages)
		.def_readwrite("larger_edge_overlap_percentages", &Matching::larger_edge_overlap_percentages)
		.def_readwrite("smaller_face_overlap_percentages", &Matching::smaller_face_overlap_percentages)
		.def_readwrite("smaller_edge_overlap_percentages", &Matching::smaller_edge_overlap_percentages)
		.def("__repr__",
			[](const Matching& matching) {
				return matching.json();
			});
	m.def("match_parts", &match_parts);
	m.def("match_parts_dict", &match_parts_dict);
	m.def("get_export_id_types", &get_export_id_types);
	m.def("overlap_parts_dict", &overlap_parts_dict);
	m.def("get_topo_id_vs_export_id", &get_topo_id_vs_export_id);
}