import os
from pathlib import Path
from femtetutils import util

femtet_dir_path = None


def get_femtet_dir():
    global femtet_dir_path

    if femtet_dir_path is None:

        # read FEMTET_ROOT_DIR if exists
        femtet_dir_path = os.environ.get('FEMTET_ROOT_DIR', None)

    if femtet_dir_path is None:
        # get Femtet root dir
        femtet_exe_path = util.get_femtet_exe_path()
        femtet_dir_path = os.path.dirname(femtet_exe_path)

    print(femtet_dir_path)

    # If lib is not built, cannot use brepmatching.
    if not os.path.exists(os.path.join(femtet_dir_path, 'lib')):
        raise FileNotFoundError('Femtet >= 2025.0.0 required. '
                                f'Your Femtet in {femtet_dir_path}'
                                ' (with macros enabled) '
                                'appears to be less than 2025.0.0.')

    return femtet_dir_path


os.add_dll_directory(rf"{get_femtet_dir()}")  # pskernel.dll の存在するパス

if os.environ.get('SA_LIB_DIR') is None:
    os.add_dll_directory(rf"{get_femtet_dir()}\lib\sa_lib\bin")  # sa_lib.dll の存在するパス
else:
    os.add_dll_directory(os.environ.get('SA_LIB_DIR'))

if os.environ.get('CM_LIB_DIR') is None:
    os.add_dll_directory(rf"{get_femtet_dir()}\lib\cm_lib\bin")  # cm_lib.dll の存在するパス
else:
    os.add_dll_directory(os.environ.get('CM_LIB_DIR'))

if os.environ.get('BREPLOADER_DIR') is None:
    os.add_dll_directory(rf"{get_femtet_dir()}\lib\breploader\bin")  # breploader.dll の存在するパス
else:
    os.add_dll_directory(os.environ.get('BREPLOADER_DIR'))

os.add_dll_directory(rf"{get_femtet_dir()}\lib\ps_session\bin")  # ps_session の存在するパス
