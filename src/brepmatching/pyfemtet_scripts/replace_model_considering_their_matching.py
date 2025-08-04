import logging
import sys

import os
from win32com.client import Dispatch, CDispatch, constants
from femtetutils.constant import FemtetClassName

from brepmatching.pyfemtet_scripts import Predictor

# point constants
POINT1 = Dispatch(FemtetClassName.CGaudiPoint)
POINT2 = Dispatch(FemtetClassName.CGaudiPoint)
(POINT1.X, POINT1.Y, POINT1.Z) = (-500, -500, -500)
(POINT2.X, POINT2.Y, POINT2.Z) = (500, 500, 500)

# logger
logger = logging.getLogger(__name__)
if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt=logging.BASIC_FORMAT)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


predictor: Predictor = None


class ModelUpdater:

    def update_model_with_prediction(
            self,
            Femtet: CDispatch,
            rebuild_fun: callable,
            parasolid_version=None,
            threshold=0.7,
            _image_path=None,
    ):
        # ===== 前提条件の処理 =====
        logger.debug('入力を処理しています。')

        # parasolid_version
        if parasolid_version is None:
            parasolid_version = constants.PARASOLID_VER_30_1_C

        # ===== 現在の Femtet に存在するモデルを取得する =====
        logger.debug('現在の Femtet のモデルをエクスポートしています。')

        # ボディキーを取得する
        succeed, all_bodies = Femtet.Gaudi.FindBodyAllByBox_py(
            Point1 := POINT1,
            Point2 := POINT2,
        )
        if not succeed: Femtet.ShowLastError()

        # ボディ数は 1 でないと非対応
        assert len(all_bodies) == 1, 'ボディ数 1 を超える場合は matching は非対応です。'

        # パスを作る
        current_xt_path = os.path.abspath('_tmp_current.x_t')  # どこでもいいが絶対パス形式であること

        # 念のため存在していれば削除する
        if os.path.exists(current_xt_path):
            os.remove(current_xt_path)

        # エクスポート
        succeed = Femtet.Gaudi.Export_py(
            FileName := current_xt_path,
            expBodies := all_bodies,
            ExpVer := parasolid_version,
            bForce := True
        )
        if not succeed: Femtet.ShowLastError()

        # 一応実行できたか確認する
        if not os.path.exists(current_xt_path):
            raise RuntimeError(
                f'Femtet のモデルを{current_xt_path}に'
                '出力することに失敗しました。'
            )


        # ===== モデルを置き換える前に境界条件の情報を取得する =====
        logger.debug('現在の Femtet の境界条件とトポロジーの対応を取得しています。')

        # すべてのトポロジーを取得する
        succeed, vertices, edges, faces = Femtet.Gaudi.FindTopologyAllByBox_py(POINT1, POINT2)
        if not succeed: Femtet.ShowLastError()

        # トポロジー ID に対して境界条件を調べる
        topo_id_vs_boundaries_org = {}
        for topo in vertices:
            boundary_names = [topo.Boundary(i) for i in range(topo.BoundaryNum)]
            id_ = topo.ID
            assert id_ not in topo_id_vs_boundaries_org.keys(), "重複したトポロジーID"
            if len(boundary_names) > 0:
                topo_id_vs_boundaries_org[id_] = boundary_names
        for topo in edges:
            boundary_names = [topo.Boundary(i) for i in range(topo.BoundaryNum)]
            id_ = topo.ID
            assert id_ not in topo_id_vs_boundaries_org.keys(), "重複したトポロジーID"
            if len(boundary_names) > 0:
                topo_id_vs_boundaries_org[id_] = boundary_names
        for topo in faces:
            boundary_names = [topo.Boundary(i) for i in range(topo.BoundaryNum)]
            id_ = topo.ID
            assert id_ not in topo_id_vs_boundaries_org.keys(), "重複したトポロジーID"
            if len(boundary_names) > 0:
                topo_id_vs_boundaries_org[id_] = boundary_names


        # ===== モデルを置き換える =====
        logger.debug('新しいモデルに置き換えています。')
        rebuild_fun()

        # ===== 置き換えたモデルをエクスポートする =====
        logger.debug('新しいモデルをもとに再構築されたモデルをエクスポートしています。')

        # ボディキーを取得する
        succeed, all_bodies = Femtet.Gaudi.FindBodyAllByBox_py(
            Point1 := POINT1,
            Point2 := POINT2,
        )
        if not succeed: Femtet.ShowLastError()

        # ボディ数は 1 でないと非対応
        assert len(all_bodies) == 1, '再構築するとボディ数が 1 を超えました。この場合は matching は非対応です。'

        # パスを作る
        var_xt_path = os.path.abspath('_tmp_variance.x_t')

        # 念のため存在していれば削除する
        if os.path.exists(var_xt_path):
            os.remove(var_xt_path)

        # エクスポート
        succeed = Femtet.Gaudi.Export_py(
            FileName := var_xt_path,
            expBodies := all_bodies,
            ExpVer := parasolid_version,
            bForce := True
        )
        if not succeed: Femtet.ShowLastError()

        # 一応実行できたか確認する
        if not os.path.exists(var_xt_path):
            raise RuntimeError(
                'Femtet の Import コマンドでインポートしたモデルを'
                '出力することに失敗しました。'
            )


        # ===== マッチングを作る =====
        logger.debug('以前のモデルと新しいモデルのトポロジーの対応を計算しています。')

        # マッチングを作る
        exp_id_map = predictor.predict(
            current_xt_path,
            var_xt_path,
            threshold=threshold,
            _image_path=_image_path,
        )

        logger.debug(f'{current_xt_path=}')
        logger.debug(f'{var_xt_path=}')

        # export id と topology id の変換を取得する
        # noinspection PyUnresolvedReferences
        from coincidence_matching import get_topo_id_vs_export_id
        topo_id_vs_exp_id_org = get_topo_id_vs_export_id(current_xt_path, Femtet.hWnd)
        topo_id_vs_exp_id_var = get_topo_id_vs_export_id(var_xt_path, Femtet.hWnd)

        # matching を topology id から topology id へのマップにする
        def get_topo_id_from_exp_id(exp_id, topo_id_vs_exp_id):
            for _topo_id, _exp_id in topo_id_vs_exp_id.items():
                if exp_id == _exp_id:
                    return _topo_id
            raise RuntimeError(f'{exp_id} is not found in specified map')

        topo_id_map = {}
        for exp_id_org, exp_id_var in exp_id_map.items():
            topo_id_org = get_topo_id_from_exp_id(exp_id_org, topo_id_vs_exp_id_org)
            topo_id_var = get_topo_id_from_exp_id(exp_id_var, topo_id_vs_exp_id_var)
            topo_id_map[topo_id_org] = topo_id_var

        # 新しいトポロジー ID に対して割り振られる境界条件を列挙する
        topo_id_vs_boundaries_var = {}
        for topo_id_org, boundary_names in topo_id_vs_boundaries_org.items():
            assert topo_id_org in topo_id_map.keys(), f'境界条件が与えられたトポロジー {topo_id_org} のマッチング相手が見つかりませんでした。'
            topo_id_var = topo_id_map[topo_id_org]
            topo_id_vs_boundaries_var[topo_id_var] = boundary_names


        # ===== モデルだけを置き換えた現在のプロジェクトから境界条件をすべて remove する =====
        logger.debug('プロジェクトから古いトポロジー番号に割り当てられた境界条件を削除しています。')

        succeed, vertices, edges, faces = Femtet.Gaudi.FindTopologyAllByBox_py(POINT1, POINT2)
        if not succeed: Femtet.ShowLastError()

        for topo in vertices:
            boundary_names = [topo.Boundary(i) for i in range(topo.BoundaryNum)]
            for boundary_name in boundary_names:
                succeed = topo.RemoveBoundary(boundary_name)
                if not succeed: Femtet.ShowLastError()
        for topo in edges:
            boundary_names = [topo.Boundary(i) for i in range(topo.BoundaryNum)]
            for boundary_name in boundary_names:
                succeed = topo.RemoveBoundary(boundary_name)
                if not succeed: Femtet.ShowLastError()
        for topo in faces:
            boundary_names = [topo.Boundary(i) for i in range(topo.BoundaryNum)]
            for boundary_name in boundary_names:
                succeed = topo.RemoveBoundary(boundary_name)
                if not succeed: Femtet.ShowLastError()
        Femtet.Gaudi.ReExecute()
        Femtet.Redraw()


        # ===== 境界条件を付けなおす =====
        logger.debug('古いトポロジー番号に対応する新しいトポロジー番号に境界条件を再割り当てしています。')

        succeed, vertices, edges, faces = Femtet.Gaudi.FindTopologyAllByBox_py(POINT1, POINT2)
        if not succeed: Femtet.ShowLastError()

        for topo in vertices:
            if topo.ID in topo_id_vs_boundaries_var.keys():
                boundaries = topo_id_vs_boundaries_var[topo.ID]
                for boundary in boundaries:
                    succeed = topo.SetBoundary(boundary)
                    if not succeed: Femtet.ShowLastError()
        for topo in edges:
            if topo.ID in topo_id_vs_boundaries_var.keys():
                boundaries = topo_id_vs_boundaries_var[topo.ID]
                for boundary in boundaries:
                    succeed = topo.SetBoundary(boundary)
                    if not succeed: Femtet.ShowLastError()
        for topo in faces:
            if topo.ID in topo_id_vs_boundaries_var.keys():
                boundaries = topo_id_vs_boundaries_var[topo.ID]
                for boundary in boundaries:
                    succeed = topo.SetBoundary(boundary)
                    if not succeed: Femtet.ShowLastError()

        Femtet.Gaudi.ReExecute()
        Femtet.Redraw()


        # ===== 一時ファイルを削除する =====
        logger.debug('一時ファイルを削除しています。')
        if os.path.exists(current_xt_path):
            os.remove(current_xt_path)
        if os.path.exists(var_xt_path):
            os.remove(var_xt_path)

    def __init__(self, Femtet):
        global predictor
        if predictor is None:
            logger.debug('Predictor を起動しました。')
            predictor = Predictor(Femtet)
        else:
            logger.debug('Predictor はすでに起動しています。')

    def __del__(self):
        self.quit()

    def quit(self):
        global predictor
        if predictor is not None:
            del predictor
            logger.debug('Predictor は終了されました。')
            predictor = None


if __name__ == '__main__':
    from time import sleep
    Femtet_ = Dispatch('FemtetMacro.Femtet')
    while Femtet_.hWnd <= 0:
        sleep(1)

    model_updator = ModelUpdater(Femtet_)

    def update_model():
        if not Femtet_.UpdateVariable('r', 4):
            Femtet_.ShowLastError()
        if not Femtet_.UpdateVariable('r2', 4):
            Femtet_.ShowLastError()
        if not Femtet_.UpdateVariable('r3', 4):
            Femtet_.ShowLastError()
        Femtet_.Gaudi.LastXTPath = r'C:\temp\model_var.x_t'
        Femtet_.Gaudi.ReExecute()
        Femtet_.Redraw()

    model_updator.update_model_with_prediction(
        Femtet=Femtet_,
        rebuild_fun=update_model
    )

    model_updator.quit()
