import os
from pathlib import Path
from time import sleep

from tqdm import tqdm
from onshape_client import Client as NewClient

from scripts.client import Client


here = Path(os.path.dirname(__file__))


paths = {
    'OriginalBrepsPath':      here / 'data' / 'original_parasolid',
    'OnshapeBaselinesPath':   here / 'data' / 'my_dataset' / "dataset" / "data" / 'baseline',
    'VariationDataPath':      here / 'data' / 'my_dataset' / "dataset" / "data" / "VariationData",
    'BrepsWithReferencePath': here / 'data' / 'my_dataset' / "dataset" / "data" / "BrepsWithReference",
    'MatchesPath':            here / 'data' / 'my_dataset' / "dataset" / "data" / "Matches",
}

dataset_path = here / 'data' / 'dataset.zip'


def get_onshape_clients():
    stacks = {
        'cad': 'https://cad.onshape.com'
    }
    c = Client(stack=stacks['cad'], logging=False)
    newClient = NewClient(
        keys_file=Path.joinpath(Path.home(), '.config', 'onshapecreds.json'),
        stack_key='https://cad.onshape.com',
    )
    return c, newClient


def wait(sec, cmd):
    for _ in tqdm(range(sec), f'wait {sec} sec for {cmd}', position=1, leave=False):
        sleep(1)


def zip_dataset_dir():
    from subprocess import run
    run([
        'powershell',
        str(here / 'data' / 'dataset_to_train' / 'create_zip.ps1')
    ])
