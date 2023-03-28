from pathlib import Path
from itertools import chain
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix


fileset = Path('/home/xiexi/cuda_projects/hpc_data/').glob('*.block4')

for file in fileset:
    if file.stem == 'cora_modify':
        continue
    if not (file.stem == 'cora' or file.stem == 'youtube' or file.stem == 'artist' or file.stem == 'pubmed' or file.stem == 'reddit.dgl' or file.stem == 'ppa' or file.stem == 'protein'):
        continue
    print(file.stem)

    indptr = np.fromfile('/home/xiexi/cuda_projects/hpc_data/' + file.stem + ".graph.ptrdump", dtype=np.int32)
    indices = np.fromfile('/home/xiexi/cuda_projects/hpc_data/' + file.stem + ".graph.edgedump", dtype=np.int32)
    v_num = len(indptr) - 1
    e_num = len(indices)
    vals = np.ones(e_num)
    csr = csr_matrix((vals, indices, indptr))

    warp_row = []
    warp_loc = []
    warp_len = []

    deg_bound = 12*32
    num_warps = 12

    warp_max_nz = deg_bound // num_warps

    cur_loc = 0
    for i in range(v_num):
        cur_degree = indptr[i+1] - indptr[i]
        if cur_degree == 0:
            continue
        tmp_loc = 0
        while True:
            warp_row.append(i)
            warp_loc.append(cur_loc)
            if cur_degree - tmp_loc <= warp_max_nz:
                warp_len.append(cur_degree - tmp_loc)
                cur_loc += cur_degree - tmp_loc
                break
            else:
                warp_len.append(warp_max_nz)
                cur_loc += warp_max_nz
                tmp_loc += warp_max_nz

    # warp_row = np.array(warp_row)
    # warp_loc = np.array(warp_loc)
    # warp_len = np.array(warp_len)
    #
    # dim = 32
    # vin = np.zeros([len(indptr) - 1, dim])
    # k = 0
    # for i in range(len(indptr) - 1):
    #     for j in range(dim):
    #         vin[i,j] = 0.01 * k
    #         k += 1
    #
    # res = csr * vin

    pad = np.zeros_like(warp_row)

    warp_4 = np.dstack([warp_row, warp_loc, warp_len, pad]).flatten()

    warp_4.astype(np.int32).tofile('./warp_4/' + file.stem + '.warp4')


