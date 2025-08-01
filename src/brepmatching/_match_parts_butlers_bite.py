"""Butlers bite

To avoid match_parts terminating with an error
on specific data during training, a script to
run match_parts in a separate process and check
whether match_parts can be run on that data.
"""

import sys
from zipfile import ZipFile
from coincidence_matching import match_parts, match_parts_dict, get_export_id_types

if __name__ == '__main__':

    zip_path = sys.argv[1]
    orig_path = sys.argv[2]
    var_path = sys.argv[3]
    hWnd = sys.argv[4]

    with ZipFile(zip_path, 'r') as zf:
        with zf.open(orig_path, 'r') as f:
            orig_part_data = f.read().decode('utf-8')
        with zf.open(var_path, 'r') as f:
            var_part_data = f.read().decode('utf-8')

    match_parts(orig_part_data, var_part_data, False, int(hWnd))
