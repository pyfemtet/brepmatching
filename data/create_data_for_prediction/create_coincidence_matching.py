import os
import re
import zipfile
import json
from pprint import pprint
from glob import glob

from coincidence_matching import (
    Matching,
    match_parts,
    match_parts_dict,
    overlap_parts_dict,
    get_export_id_types,
)

# get the directory where this script exists
here = os.path.dirname(__file__)


def prepare_predict(
        exact=False,
        zip_filename='data_to_predict.zip',
        silent=False,
):
    """Do coincidence matching, make json file and create zip file to predict matching.

    Premise:
        <some_directory>
          ├ create_coincidence_matching.py
          ├ (result zip created here)
          └ data
              ├ BrepsWithReference
              │   ├ <parasolid-name-endswith-V0>.x_t
              │   ├ <parasolid-name-endswith-V1>.x_t
              │   ├ <parasolid-name-endswith-V2>.x_t
              │   ├ ...
              │
              ├ Matches
              └ VariationData
                  ├ all_variations.csv
                  └ all_models.csv

    Args:
        exact(bool, optional): If False, matching process allows overlaps. Defaults to False.
        zip_filename(str, optional): Result file name.
        silent(bool, optional: If True, print nothing. Defaults to False.

    """

    # make each .json (~~~V0.x_t vs ~~~Vn.x_t) inside BrepsWithReference to Matches directory
    target_dir = os.path.join(here, 'data', 'BrepsWithReference')
    for path in glob(os.path.join(target_dir, '*.x_t')):
        if not silent: print(path)

        # If not V0, make json
        if not os.path.splitext(path)[0].endswith('0'):
            # get V0 and Vn filename
            vn_filename = os.path.basename(path)
            v0_filename = re.sub(r'^(.*?V)\d\.x_t$', r'\g<1>0.x_t', vn_filename)

            make_matching_data_json(
                filename_orig=v0_filename,
                filename_var=vn_filename,
                exact=exact,
                silent=silent,
            )

    # create zip
    create_zip_from_directory(
        zip_filename=zip_filename,
        source_directory=os.path.join(here, 'data')
    )


def make_matching_data_json(
        filename_orig: str,
        filename_var: str,
        exact=False,
        silent=False,
):
    """Do coincidence matching and make json file.

    Premise:
        <some_directory>
          ├ create_coincidence_matching.py
          └ data
              ├ BrepsWithReference
              │   ├ <parasolid-name-endswith-V0>.x_t
              │   ├ <parasolid-name-endswith-V1>.x_t
              │   ├ <parasolid-name-endswith-V2>.x_t
              │   ├ ...
              │
              ├ Matches
              └ VariationData
                  ├ all_variations.csv
                  └ all_models.csv

    Args:
        filename_orig(str): <parasolid-name-endswith-V0>. Ends with 'V0'.
        filename_var(str): <parasolid-name-endswith-Vn>. Ends with 'Vn', n is an single digit positive integer.
        exact(bool, optiona): If False, matching process allows overlaps. Defaults to False.
        silent(bool, optional: If True, print nothing. Defaults to False.

    """

    # set filename
    filename_orig = filename_orig[:-4] if filename_orig.endswith('.x_t') else filename_orig
    filename_var = filename_var[:-4] if filename_var.endswith('.x_t') else filename_var

    # get versions
    version_suffix_var = filename_var[-1]

    # files are in <here>/data/BrepsWithReference/...
    path_orig = os.path.join(here, 'data', 'BrepsWithReference', filename_orig + '.x_t')
    path_var = os.path.join(here, 'data', 'BrepsWithReference', filename_var + '.x_t')

    # get data
    with open(path_orig, "r") as f:
        orig_data = f.read()
    with open(path_var, "r") as f:
        var_data = f.read()

    # calc coincidence matching
    matches: dict = match_parts_dict(orig_data, var_data, exact)

    # get id types for debug
    id_and_types: dict[[str], str] = get_export_id_types(orig_data)

    # make json from coincidence match result
    out = {}
    for i, (k, v) in enumerate(matches.items()):
        out.update(
            {
                i: {
                    "val1": k,
                    "val2": v,
                }
            }
        )
        if not silent: print(f'{id_and_types[k]} {k} matches {v}')

    if not silent:
        print()
        print('===== json =====')
        pprint(out)

    # save json to <here>/data/Matches/...
    json_path = os.path.join(
        here,
        'data',
        'Matches',
        filename_orig + version_suffix_var + '.json'  # i.e. ~~~V01.json
    )

    with open(json_path, "w") as f:
        json.dump(out, f)


def create_zip_from_directory(zip_filename, source_directory):
    basename = os.path.basename(source_directory)

    # Create a ZipFile object
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Walk through all directories and files in the source directory
        for foldername, subfolders, filenames in os.walk(source_directory):
            for filename in filenames:
                if filename == 'desktop.ini':
                    continue
                if filename == '.gitignore':
                    continue
                # Create a complete file path
                file_path = os.path.join(foldername, filename)
                # Write the file to the zip file using relative paths
                arcname = os.path.relpath(file_path, start=source_directory)
                arcname = os.path.join(basename, arcname)
                zip_file.write(file_path, arcname)


if __name__ == '__main__':
    # make_matching_data_json(
    #     '134ea4c9f8e1c24ee2333eed_599c0b6979b89fb7593030a6_05b80ff642e652a00427e321_default_jjeeiV0.x_t',
    #     '134ea4c9f8e1c24ee2333eed_599c0b6979b89fb7593030a6_05b80ff642e652a00427e321_default_jjeeiV1.x_t'
    # )

    # create_zip_from_directory(
    #     os.path.join('data_to_predict.zip'),
    #     os.path.join(here, 'data')
    # )

    prepare_predict(
        zip_filename='../data_to_predict.zip',
        exact=False,
        silent=False,
    )

# # =====================
#
# ret: Matching = match_parts(orig_data, var_data, True)
#
# print(ret)
# print(ret.face_matches)
# print(ret.edge_matches)
# print(ret.vertex_matches)
#
#
# ret: Matching = match_parts(orig_data, var_data, False)
#
# print(ret)
# print(ret.face_matches)
# print(ret.edge_matches)
# print(ret.vertex_matches)
#
#
# ret: dict = match_parts_dict(orig_data, var_data, True)
# print(ret)
#
# ret: dict = match_parts_dict(orig_data, var_data, False)
# print(ret)
#
#
# ret: dict[[str], str] = get_export_id_types(orig_data)
# print(ret)
