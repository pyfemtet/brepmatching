from pathlib import Path

import pandas as pd

from client import Client
from onshape_client import Client as NewClient
import matchGenHelpFunctions as mg


folder = 'my_dataset'
baselineFolder = 'baselineOnshapeIlyaFixFullRun'

if __name__ == '__main__':

    stacks = {
        'cad': 'https://cad.onshape.com'
    }
    c = Client(stack=stacks['cad'], logging=False)

    newClient = NewClient(
        keys_file=Path.joinpath(Path.home(), '.config', 'onshapecreds.json'),
        stack_key='https://cad.onshape.com',
    )

    paths = {
        'OriginalBrepsPath': Path().cwd().parents[0] / 'data' / "OriginalBreps/with_tol",
        'OnshapeBaselinesPath': Path().cwd().parents[0] / 'data' / folder / "data" / baselineFolder,
        'VariationDataPath': Path().cwd().parents[0] / 'data' / folder / "data" / "VariationData",
        'BrepsWithReferencePath': Path().cwd().parents[0] / 'data' / folder / "data" / "BrepsWithReference",
        'MatchesPath': Path().cwd().parents[0] / 'data' / folder / "data" / "Matches",
    }

    # get model info and referenced parasolid via Onshape
    orinalModelInfo, orginReferences = mg.initNewModel(c, paths, modelName='my_model')

    # get variated model by same way
    # varInfo: dict = mg.createVariation(c, paths, 1, orinalModelInfo, orginReferences, False, False)
    varInfo: dict = mg.init_var_model(c, paths, 'my_model_var', 0, orinalModelInfo)

    # make csv
    orinalModelInfo['nVariations'] = 1  # update
    all_models_path = paths['VariationDataPath'] / 'all_models.csv'
    pd.Series(orinalModelInfo).to_frame().transpose().to_csv(all_models_path, index=False)

    all_variations_path = paths['VariationDataPath'] / 'all_variations.csv'
    pd.Series(varInfo).to_frame().transpose().to_csv(all_variations_path, index=False)

