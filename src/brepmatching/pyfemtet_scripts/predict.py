import os
import pytorch_lightning as pl
from brepmatching.matching_model import MatchingModel
from brepmatching.data import BRepMatchingDataModule
from torch_geometric.loader import DataLoader
import torch
from time import time

from brepmatching.matching_model import InitStrategy
from brepmatching.data import BRepMatchingDataset

import logging
import warnings

console_logger = logging.getLogger('BRepMatching')
logging.getLogger("pytorch_lightning").setLevel(logging.ERROR)

warnings.filterwarnings("ignore", ".*`max_epochs` was not set*")


def predict_brepmatching(zip_path, hWnd, threshold=0.7, image_path=None) -> dict:

    checkpoint_path = os.path.join(
        os.path.dirname(__file__),
        'epoch=358-val_loss=0.005953.ckpt'
    )

    # DataModule
    console_logger.debug('===== data load start =====')
    start = time()
    data = BRepMatchingDataModule(
        batch_size=1,
        num_workers=0,
        persistent_workers=False,
        # shuffle: bool = True,
        zip_path=zip_path,
        # cache_path: str = None,
        # debug_data: bool = False,
        seed=None,  # or 42
        test_size=0,
        val_size=0,
        single_set=True,
        # test_identity: bool = False,
        # exact_match_labels: bool = False,
        # val_batch_size: int = None,
        # test_batch_size: int = None,
        # enable_blacklist: bool = True,
    )
    console_logger.debug(f"===== data load ended with {int(time() - start)} sec. =====")

    # Model
    model = MatchingModel()
    model.load_state_dict(
        torch.load(
            checkpoint_path,
            map_location=torch.device('cpu'),
            weights_only=True,  # Note
        )['state_dict'],
    )
    # Note:
    #   Caught following warning when update to torch >= 2.
    #     FutureWarning: You are using `torch.load` with `weights_only=False`
    #     (the current default value), which uses the default pickle module
    #     implicitly. It is possible to construct malicious pickle data which
    #     will execute arbitrary code during unpickling
    #     (See https://github.com/pytorch/pytorch/blob/main/SECURITY.md#untrusted-models
    #     for more details). In a future release, the default value for `weights_only`
    #     will be flipped to `True`. This limits the functions that could be executed
    #     during unpickling. Arbitrary objects will no longer be allowed to be loaded
    #     via this mode unless they are explicitly allowlisted by the user via
    #     `torch.serialization.add_safe_globals`. We recommend you start setting
    #     `weights_only=True` for any use case where you don't have full control of
    #     the loaded file. Please open an issue on GitHub for any issues related to
    #     this experimental feature.
    #       model.load_state_dict(torch.load(checkpoint_path, map_location=torch.device('cpu'))['state_dict'])
    #   But the prediction using existing .ckpt (serialized without
    #   torch.serialization.add_safe_globals) passed the test.
    #   So the re-training is not necessary.
    callbacks = model.get_callbacks()

    # Trainer
    trainer = pl.Trainer(
        logger=False,
        callbacks=callbacks,
    )

    # ===== predict =====
    # data setup
    console_logger.debug('===== data.setup() start =====')
    start = time()
    id_map: list[dict[str, dict]] = data.setup(export_id_map=True, hWnd=hWnd)
    """id_map (dict): hashed Tensor to BTI/ExportedID
    
    id_map[0]: id_maps of model 1.
    id_map[0]['f']: dict
    
    """
    console_logger.debug(f"===== data.setup() ended with {int(time() - start)} sec. =====")

    # declare Lightning objects with type hint
    trainer: pl.Trainer = trainer
    data_module: BRepMatchingDataModule = data
    data_set: BRepMatchingDataset = data_module.train_ds
    data_loader: DataLoader = data_module.predict_dataloader()
    loss_tensor: torch.Tensor = None
    hetdata_batch_after: 'HetDataBatch' = None

    # pick a HetDataBatch
    console_logger.debug('===== hetdata_batch start =====')
    start = time()
    hetdata_batch = next(iter(data_loader))  # if n_workers == 20, take 94 sec.
    console_logger.debug(f"===== hetdata_batch ended with {int(time() - start)} sec. =====")

    # start prediction
    console_logger.debug('===== prediction start =====')
    start = time()
    loss_tensor, hetdata_batch_after = model.do_iteration(
        hetdata_batch.clone(),
        threshold,  # threshold. by paper, 0.7.
        InitStrategy,
        False  # use adjacency or not.
    )
    console_logger.debug(f"===== prediction ended with {int(time() - start)} sec. =====")

    # ===== construct ExportedID matchings =====
    # get hashed match
    id_matches = {}
    for model1_topo, model2_topo in hetdata_batch_after.cur_faces_matches.detach().numpy().T:
        id_matches.update(
            {id_map[0]['f'][model1_topo]: id_map[1]['f'][model2_topo]}
        )
    for model1_topo, model2_topo in hetdata_batch_after.cur_edges_matches.detach().numpy().T:
        id_matches.update(
            {id_map[0]['e'][model1_topo]: id_map[1]['e'][model2_topo]}
        )
    for model1_topo, model2_topo in hetdata_batch_after.cur_vertices_matches.detach().numpy().T:
        id_matches.update(
            {id_map[0]['v'][model1_topo]: id_map[1]['v'][model2_topo]}
        )

    # # Save match prediction result
    # with open(os.path.join(os.path.dirname(__file__), 'predicted_id_matches.json'), 'w', encoding='utf-8') as f:
    #     json.dump(id_matches, f)

    # ===== rendering result =====
    if image_path:
        from brepmatching.visualization import render_predictions, show_image

        im = show_image(
            render_predictions(
                hetdata_batch_after,
                face_match_preds=hetdata_batch_after.cur_faces_matches,
                edge_match_preds=hetdata_batch_after.cur_edges_matches,
                vertex_match_preds=hetdata_batch_after.cur_vertices_matches,
            )
        )
        im.save(image_path)

    return id_matches
