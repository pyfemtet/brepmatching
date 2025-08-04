import os
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import shutil

import set_attributes as sa
from brepmatching.pyfemtet_scripts.create_coincidence_matching import make_matching_data_json


def embed_bti_export_id(src_path, dst_path, hWnd):
    if not os.path.exists(src_path):
        raise FileNotFoundError(f'{src_path} is not found.')

    # path を正規化します。
    if isinstance(src_path, Path):
        src_path = str(src_path.resolve())
    src_path = src_path.replace('/', '\\')
    if isinstance(dst_path, Path):
        dst_path = str(dst_path.resolve()).replace('/', '\\')
    dst_path = dst_path.replace('/', '\\')

    # 上書きしたい場合、buf_path に出力してから src_path に上書きします。
    if src_path == dst_path:
        # buf_path を作成します。
        buf_path = os.path.splitext(src_path)[0] + '_tmp.x_t'

        # buf_path に出力します。
        if os.path.exists(buf_path):
            os.remove(buf_path)
        sa.set_attributes_to_xt(src_path, buf_path, hWnd)

        # src_path のファイルを削除します。
        if os.path.exists(src_path):
            os.remove(src_path)

        # buf_path を src_path にリネームします。
        os.rename(buf_path, src_path)

        # buf_path のファイルを削除します。
        if os.path.exists(buf_path):
            os.remove(buf_path)

    # 上書きしない場合
    else:
        if os.path.exists(dst_path):
            os.remove(dst_path)
        sa.set_attributes_to_xt(src_path, dst_path, hWnd)


class DatasetCreatorToPredict(object):
    BASE_MODEL_NAME = 'model'  # If change this, change csv template too.

    def __init__(self, Femtet):
        # Prepare temporary folder
        self.dataset_workspace = TemporaryDirectory()
        self.dataset_workspace_path = self.dataset_workspace.name

        # Femtet
        self.Femtet = Femtet

        # termination flag
        self._terminated = False

    @property
    def target_dir(self):
        return os.path.join(self.dataset_workspace_path, 'data', 'dataset_to_predict', 'dataset', 'data')

    def _init_workspace(self):
        # remove existing directory
        if os.path.exists(self.target_dir):
            shutil.rmtree(self.target_dir)

        # re-create new directory
        os.makedirs(self.target_dir)
        os.makedirs(os.path.join(self.target_dir, 'BrepsWithReference'))
        os.makedirs(os.path.join(self.target_dir, 'Matches'))

        # copy VariationData files from template
        # (These files are listed in pyproject.toml)
        shutil.copytree(
            src=os.path.join(os.path.dirname(__file__), 'data/dataset_to_predict/dataset/data/VariationData'),
            dst=os.path.join(self.target_dir, 'VariationData')
        )

    def _compress_workspace(self) -> str:
        # get dataset folder path
        dataset_path = os.path.join(self.target_dir, '..')  # tmp_~~/data/dataset_to_predict/dataset

        # get dataset.zip path
        zip_file_path = os.path.join(self.dataset_workspace_path, 'dataset_to_predict.zip')

        # check
        if not os.path.exists(dataset_path):
            raise RuntimeError(f"The directory {dataset_path} did not be created.")

        # create zip and add all files inside dataset folder
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(dataset_path):
                for file in files:
                    # get relpath from abspath
                    full_path = os.path.join(root, file)
                    arc_name = os.path.relpath(full_path, start=dataset_path)
                    zf.write(full_path, arc_name)

        return zip_file_path

    def create(self, xt_path_0, xt_path_1) -> str:
        # re-init workspace
        self._init_workspace()

        # create attributed .x_t
        # and pack the path to .txt
        embed_bti_export_id(xt_path_0, xt_path_0, self.Femtet.hWnd)
        xt_alt_path_0 = os.path.join(self.target_dir, 'BrepsWithReference', self.BASE_MODEL_NAME + 'V0.x_t')
        with open(xt_alt_path_0, 'w', encoding='utf-8') as f:
            f.write(os.path.abspath(xt_path_0).replace('/', '\\'))

        embed_bti_export_id(xt_path_1, xt_path_1, self.Femtet.hWnd)
        xt_alt_path_1 = os.path.join(self.target_dir, 'BrepsWithReference', self.BASE_MODEL_NAME + 'V1.x_t')
        with open(xt_alt_path_1, 'w', encoding='utf-8') as f:
            f.write(os.path.abspath(xt_path_1).replace('/', '\\'))

        # create match json, csv files
        make_matching_data_json(
            self.BASE_MODEL_NAME + 'V0',
            self.BASE_MODEL_NAME + 'V1',
            exact=False,
            silent=True,
            wkdir=os.path.abspath(os.path.join(self.target_dir, '..')),
            Femtet=self.Femtet,
        )

        # compress them
        zip_path = self._compress_workspace()

        return zip_path

    def close(self):
        # remove temporary folder
        self.dataset_workspace.cleanup()
        