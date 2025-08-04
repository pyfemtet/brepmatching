import os
from contextlib import closing
from brepmatching.pyfemtet_scripts import Predictor

from win32com.client import Dispatch
Femtet = Dispatch('FemtetMacro.Femtet')


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))

    # initialize
    predictor = Predictor(Femtet)

    # Remove temporary folder
    # after test finished
    with closing(predictor):

        # predict
        id_map = predictor.predict(
            'files/Part1.x_t',
            'files/model_var.x_t',
        )
        print(id_map)

        # predict
        id_map = predictor.predict(
            'files/Part1.x_t',
            'files/model_var.x_t',
        )
        print(id_map)

        # predict
        id_map = predictor.predict(
            'files/model_orig.x_t',
            'files/model_var.x_t',
        )
        print(id_map)

        # predict
        id_map = predictor.predict(
            'files/Cube.x_t',
            'files/RoundedCube.x_t',
        )
        print(id_map)
