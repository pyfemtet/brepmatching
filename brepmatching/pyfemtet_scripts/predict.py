import json
import os
import pytorch_lightning as pl
from argparse import ArgumentParser
from brepmatching.matching_model import MatchingModel
from pytorch_lightning.loggers import TensorBoardLogger
from brepmatching.data import BRepMatchingDataModule
from torch_geometric.loader import DataLoader
import torch
import parse
from time import time

# for type hint
from brepmatching.matching_model import InitStrategy
from brepmatching.data import BRepMatchingDataset

import logging
console_logger = logging.getLogger('BRepMatching')
# logging.getLogger('lightning').setLevel(0)
# pl.utilities.distributed.log.setLevel(logging.ERROR)
logging.getLogger("pytorch_lightning").setLevel(logging.ERROR)

import warnings
warnings.filterwarnings("ignore", ".*`max_epochs` was not set*")



def predict_brepmatching(zip_path, hWnd, threshold=0.7, with_image=False) -> dict:

    parser = ArgumentParser(allow_abbrev=False, conflict_handler='resolve')

    parser.add_argument('--tensorboard_path', type=str, default='.')
    parser.add_argument('--checkpoint_path', type=str, default=None)
    parser.add_argument('--name', type=str, default='unnamed')
    parser.add_argument('--resume_version', type=int, default=None)
    parser.add_argument('--best_checkpoint', type=str, default=None)
    parser.add_argument('--seed', type=int, default=None)
    parser.add_argument('--verbose', type=int, default=0)
    parser.add_argument('--logger', action='store_false')
    parser.add_argument('--no_train', action='store_true')
    parser.add_argument('--no_test', action='store_true')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--override_args', action='store_true')
    parser.add_argument('--predict', action='store_true')

    parser = pl.Trainer.add_argparse_args(parser)
    parser = BRepMatchingDataModule.add_argparse_args(parser)
    parser = MatchingModel.add_argparse_args(parser)

    args = parser.parse_args()

    # settings
    args.zip_path = zip_path
    args.num_workers = 0
    args.persistent_workers = False
    args.no_train = True
    args.batch_size = 1
    args.single_set = True
    args.val_size = 0
    args.test_size = 0
    args.checkpoint_path = os.path.join(
        os.path.dirname(__file__),
        'epoch=358-val_loss=0.005953.ckpt'
    )

    # logger = TensorBoardLogger(
    #     args.tensorboard_path,
    #     name=args.name,
    #     default_hp_metric=False,
    #     version=args.resume_version
    # )
    # logger.log_hyperparams(args)

    if args.resume_version is not None:
        # last_ckpt = os.path.join(
        #     logger.log_dir,
        #     'checkpoints',
        #     'last.ckpt'
        # )
        #
        # if not os.path.exists(last_ckpt):
        #     print(f'No last checkpoint found for version_{args.resume_version}.')
        #     print(f'Tried {last_ckpt}')
        #     exit()
        # args.checkpoint_path = last_ckpt
        # args.resume_from_checkpoint = last_ckpt
        pass

    elif args.best_checkpoint is not None:
        all_checkpoints = os.listdir(args.best_checkpoint)
        fmt = "epoch={}-val_loss={}.ckpt"
        candidates = []
        for ckpt in all_checkpoints:
            a = parse.parse(fmt, ckpt)
            if a is not None:
                epoch, val_loss = a
                candidates.append((float(val_loss), ckpt))
        if len(candidates) == 0:
            print(f"No checkpoints in {args.best_checkpoint}")
            exit()
        args.checkpoint_path = os.path.join(args.best_checkpoint,
                                            min(candidates)[1])
        console_logger.debug(f"Using checkpoint: {args.checkpoint_path}")

    console_logger.debug('===== data load start =====')
    start = time()
    data = BRepMatchingDataModule.from_argparse_args(args)
    console_logger.debug(f"===== data load ended with {int(time() - start)} sec. =====")

    if args.checkpoint_path is None:
        model = MatchingModel.from_argparse_args(args)
    elif args.override_args:
        model = MatchingModel.from_argparse_args(args)
        model.load_state_dict(torch.load(args.checkpoint_path)['state_dict'])
    else:
        model = MatchingModel.load_from_checkpoint(args.checkpoint_path)
    callbacks = model.get_callbacks()

    # trainer = pl.Trainer.from_argparse_args(args, logger=logger, callbacks=callbacks)
    trainer = pl.Trainer.from_argparse_args(args, logger=False, callbacks=callbacks)

    # ===== predict =====
    start = time()
    console_logger.debug('===== data.setup() start =====')

    id_map: list[dict[dict]] = data.setup(export_id_map=True, hWnd=hWnd)
    """id_map (dict): hashed Tensor to BTI/ExportedID
    
    id_map[0]: id_maps of model 1.
    id_map[0]['f']: 
    
    """

    console_logger.debug(f"===== data.setup() ended with {int(time() - start)} sec. =====")

    trainer: pl.Trainer = trainer
    data_module: BRepMatchingDataModule = data
    data_set: BRepMatchingDataset = data_module.train_ds
    data_loader: DataLoader = data_module.predict_dataloader()
    loss_tensor: torch.Tensor = None
    hetdata_batch_after: 'HetDataBatch' = None

    # pick a HetDataBatch
    start = time()
    console_logger.debug('===== hetdata_batch start =====')
    hetdata_batch = next(iter(data_loader))  # if n_workers == 20, take 94 sec.
    console_logger.debug(f"===== hetdata_batch ended with {int(time() - start)} sec. =====")

    start = time()
    console_logger.debug('===== prediction start =====')
    # do_iteration
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
    if with_image:
        from brepmatching.visualization import render_predictions, show_image

        im = show_image(
            render_predictions(
                hetdata_batch_after,
                face_match_preds=hetdata_batch_after.cur_faces_matches,
                edge_match_preds=hetdata_batch_after.cur_edges_matches,
                vertex_match_preds=hetdata_batch_after.cur_vertices_matches,
            )
        )
        im.save(
            os.path.join(
                os.path.dirname(__file__),
                f"predict_result(threshold_{threshold}).png"
            )
        )

    return id_matches
