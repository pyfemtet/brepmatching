import os
from brepmatching.pyfemtet_scripts.predict import predict_brepmatching
from brepmatching.pyfemtet_scripts.dataset_creator_to_predict import DatasetCreatorToPredict, embed_bti_export_id


class Predictor:

    def __init__(self, Femtet):
        # initizlize (launch child process and create temporary folder)
        self.zipper = DatasetCreatorToPredict(Femtet)
        self.Femtet = Femtet

    def predict(self, xt_path1, xt_path2) -> dict:
        # create zip to temporary folder
        zip_path = self.zipper.create(xt_path1, xt_path2)

        # do predict
        return predict_brepmatching(zip_path, self.Femtet.hWnd)

    def __del__(self):
        # finish process and delete temporary folder
        del self.zipper
