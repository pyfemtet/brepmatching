from brepmatching.pyfemtet_scripts.predict import predict_brepmatching
from brepmatching.pyfemtet_scripts.dataset_creator_to_predict import DatasetCreatorToPredict


class Predictor:

    def __init__(self, Femtet):
        # initizlize (launch child process and create temporary folder)
        self.zipper = DatasetCreatorToPredict(Femtet)
        self.Femtet = Femtet

    def predict(self, xt_path1, xt_path2, threshold=0.7, _image_path=None) -> dict:
        # create zip to temporary folder
        zip_path = self.zipper.create(xt_path1, xt_path2)

        # do predict
        return predict_brepmatching(
            zip_path,
            self.Femtet.hWnd,
            threshold=threshold,
            image_path=_image_path,
        )
    
    def close(self):
        self.zipper.close()
