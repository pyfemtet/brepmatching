import torch
from automate.automate import SBGCN
from torch.nn import BatchNorm1d
from torch_geometric.nn import GeneralConv

from .utils import unzip_hetdata


class BrepNormalizer(torch.nn.Module):
    def __init__(self,
        s_face = 62,
        s_loop = 38,
        s_edge = 72):
        super().__init__()
        self.faces_bn = BatchNorm1d(s_face)
        self.edges_bn = BatchNorm1d(s_edge)
        self.loops_bn = BatchNorm1d(s_loop)
    
    def forward(self, data):
        data.faces = self.faces_bn(data.faces)
        data.edges = self.edges_bn(data.edges)
        data.loops = self.loops_bn(data.loops)
        return data


class PairEmbedder(torch.nn.Module):
    def __init__(self,
        s_face = 62,
        s_loop = 38,
        s_edge = 72,
        s_vert = 3,
        embedding_size = 64,
        k = 6,
        batch_norm=False,
        mp_exact_matches=False,
        mp_overlap_matches=False,
        prematch_layers=4,
        use_uvnet_features=False,
        crv_emb_dim=64,
        srf_emb_dim=64,
        mp_cur_matches=False,
    ):
        super().__init__()
        self.batch_norm = batch_norm
        if batch_norm:
            self.norm_left = BrepNormalizer(s_face, s_loop, s_edge)
            self.norm_right = BrepNormalizer(s_face, s_loop, s_edge)
        self.sbgcn = SBGCN(s_face, s_loop, s_edge, s_vert, embedding_size, k, use_uvnet_features=use_uvnet_features, crv_emb_dim=crv_emb_dim, srf_emb_dim=srf_emb_dim)
        self.mp_exact_matches = mp_exact_matches
        self.mp_overlap_matches = mp_overlap_matches
        self.mp_cur_matches = mp_cur_matches
        self.prematch_layers = prematch_layers
        if self.mp_exact_matches or self.mp_overlap_matches or self.mp_cur_matches:
            self.prematch_gnns = torch.nn.ModuleList(
                [GeneralConv(-1, embedding_size, -1, attention=True, heads=8)
                for i in range(self.prematch_layers)])
    
    def forward(self, batch):
        orig_batch, var_batch = unzip_hetdata(batch)
        if self.batch_norm:
            orig_batch = self.norm_left(orig_batch)
            var_batch = self.norm_right(var_batch)
        orig_embeddings = self.sbgcn(orig_batch)
        var_embeddings = self.sbgcn(var_batch)
        _, _, f_orig, l_orig, e_orig, v_orig = orig_embeddings
        _, _, f_var, l_var, e_var, v_var = var_embeddings

        for emb in [f_orig, l_orig, e_orig, v_orig, f_var, l_var, e_var, v_var]:
            assert(not emb.isnan().any())


        device = batch.left_faces.device

        if self.mp_exact_matches or self.mp_overlap_matches or self.mp_cur_matches:
            n_types = 4

            face_matches = torch.empty(0, dtype=torch.long, device=device)
            edge_matches = torch.empty(0, dtype=torch.long, device=device)
            vert_matches = torch.empty(0, dtype=torch.long, device=device)

            face_match_types = torch.empty(0, dtype=torch.long, device=device) 
            edge_match_types = torch.empty(0, dtype=torch.long, device=device) 
            vert_match_types = torch.empty(0, dtype=torch.long, device=device) 

            for is_set, fmt in [(self.mp_exact_matches, "bl_exact_%s_matches"),
                               (self.mp_overlap_matches, "bl_overlap_%s_matches"), 
                               (self.mp_cur_matches, "cur_%s_matches")]:
                if is_set:
                    face_matches = torch.cat([face_matches, batch[fmt % "faces"]], dim=1)
                    edge_matches = torch.cat([edge_matches, batch[fmt % "edges"]], dim=1)
                    

                    face_match_types = torch.cat([face_match_types, torch.full((batch[fmt % "faces"].shape[1],), n_types, device=device)])
                    edge_match_types = torch.cat([edge_match_types, torch.full((batch[fmt % "edges"].shape[1],), n_types + 1, device=device)])
                    
                    if fmt % "vertices" in batch.keys(): # There are no vertex overlaps
                        vert_matches = torch.cat([vert_matches, batch[fmt % "vertices"]], dim=1)
                        vert_match_types = torch.cat([vert_match_types, torch.full((batch[fmt % "vertices"].shape[1],), n_types + 2, device=device)])
                        n_types += 1
                    n_types += 2
            
            # Put Everything into one big graph
            
            # Combine the Nodes
            nodes = torch.cat([f_orig,f_var,l_orig,l_var,e_orig,e_var,v_orig,v_var])
            
            # Compute new node offsets
            f_orig_offset = 0
            f_var_offset = f_orig_offset + f_orig.shape[0]
            l_orig_offset = f_var_offset + f_var.shape[0]
            l_var_offset = l_orig_offset + l_orig.shape[0]
            e_orig_offset = l_var_offset + l_var.shape[0]
            e_var_offset = e_orig_offset + e_orig.shape[0]
            v_orig_offset = e_var_offset + e_var.shape[0]
            v_var_offset = v_orig_offset + v_orig.shape[0]

            # Renumber matches
            face_matches[0] = face_matches[0] + f_orig_offset
            face_matches[1] = face_matches[1] + f_var_offset
            edge_matches[0] = edge_matches[0] + e_orig_offset
            edge_matches[1] = edge_matches[1] + e_var_offset
            vert_matches[0] = vert_matches[0] + v_orig_offset
            vert_matches[1] = vert_matches[1] + v_var_offset

            # Renumber Left Graph
            left_face_to_face = batch.left_face_to_face[:2].clone()
            left_face_to_face_types = torch.full((left_face_to_face.shape[1],), 0, device=left_face_to_face.device)
            left_face_to_face[0] = left_face_to_face[0] + f_orig_offset
            left_face_to_face[1] = left_face_to_face[1] + f_orig_offset

            left_face_to_loop = batch.left_face_to_loop.clone()
            left_face_to_loop_types = torch.full((left_face_to_loop.shape[1],), 1, device=left_face_to_loop.device)
            left_face_to_loop[0] = left_face_to_loop[0] + f_orig_offset
            left_face_to_loop[1] = left_face_to_loop[1] + l_orig_offset

            left_loop_to_edge = batch.left_loop_to_edge.clone()
            left_loop_to_edge_types = torch.full((left_loop_to_edge.shape[1],), 2, device=left_loop_to_edge.device)
            left_loop_to_edge[0] = left_loop_to_edge[0] + l_orig_offset
            left_loop_to_edge[1] = left_loop_to_edge[1] + e_orig_offset

            left_edge_to_vertex = batch.left_edge_to_vertex.clone()
            left_edge_to_vertex_types = torch.full((left_edge_to_vertex.shape[1],), 3, device=left_edge_to_vertex.device)
            left_edge_to_vertex[0] = left_edge_to_vertex[0] + e_orig_offset
            left_edge_to_vertex[1] = left_edge_to_vertex[1] + v_orig_offset

            # Renumber Right Graph
            right_face_to_face = batch.right_face_to_face[:2].clone()
            right_face_to_face_types = torch.full((right_face_to_face.shape[1],), 0, device=right_face_to_face.device)
            right_face_to_face[0] = right_face_to_face[0] + f_var_offset
            right_face_to_face[1] = right_face_to_face[1] + f_var_offset

            right_face_to_loop = batch.right_face_to_loop.clone()
            right_face_to_loop_types = torch.full((right_face_to_loop.shape[1],), 1, device=right_face_to_loop.device)
            right_face_to_loop[0] = right_face_to_loop[0] + f_var_offset
            right_face_to_loop[1] = right_face_to_loop[1] + l_var_offset

            right_loop_to_edge = batch.right_loop_to_edge.clone()
            right_loop_to_edge_types = torch.full((right_loop_to_edge.shape[1],), 2, device=right_loop_to_edge.device)
            right_loop_to_edge[0] = right_loop_to_edge[0] + l_var_offset
            right_loop_to_edge[1] = right_loop_to_edge[1] + e_var_offset

            right_edge_to_vertex = batch.right_edge_to_vertex.clone()
            right_edge_to_vertex_types = torch.full((right_edge_to_vertex.shape[1],), 3, device=right_edge_to_vertex.device)
            right_edge_to_vertex[0] = right_edge_to_vertex[0] + e_var_offset
            right_edge_to_vertex[1] = right_edge_to_vertex[1] + v_var_offset
            
            # Put all the edges together
            links = torch.cat([
                left_face_to_face,
                left_face_to_loop,
                left_loop_to_edge,
                left_edge_to_vertex,
                right_face_to_face,
                right_face_to_loop,
                right_loop_to_edge,
                right_edge_to_vertex,
                face_matches,
                edge_matches,
                vert_matches
            ], dim=1)

            # Put the edge features together in the same order
            link_data = torch.cat([
                left_face_to_face_types,
                left_face_to_loop_types,
                left_loop_to_edge_types,
                left_edge_to_vertex_types,
                right_face_to_face_types,
                right_face_to_loop_types,
                right_loop_to_edge_types,
                right_edge_to_vertex_types,
                face_match_types,
                edge_match_types,
                vert_match_types
            ])

            # Make undirected
            links = torch.cat([links, links[[1,0]]],dim=1)
            link_data = torch.cat([link_data, link_data])

            # One-Hot Encode link data
            link_data = torch.nn.functional.one_hot(link_data, n_types).float()

            for gnn in self.prematch_gnns:
                nodes = gnn(
                    x = nodes,
                    edge_index = links,
                    edge_attr = link_data
                    )
            
            # Separate node types

            f_orig = nodes[0:f_var_offset]
            f_var = nodes[f_var_offset:l_orig_offset]
            l_orig = nodes[l_orig_offset:l_var_offset]
            l_var = nodes[l_var_offset:e_orig_offset]
            e_orig = nodes[e_orig_offset:e_var_offset]
            e_var = nodes[e_var_offset:v_orig_offset]
            v_orig = nodes[v_orig_offset:v_var_offset]
            v_var = nodes[v_var_offset:]

        return (f_orig, e_orig, v_orig), (f_var, e_var, v_var)