from tmap.netx.SAFE import get_SAFE_summary
import numpy as np
import itertools
from scipy.stats import pearsonr
from statsmodels.stats.multitest import fdrcorrection
from tqdm import tqdm
#
# def _pair_enrich(safe_scores, safe_summary, fea1, fea2):
#     # feature1 should be a key of the safe_scores
#     if fea1 not in safe_scores or fea2 not in safe_scores:
#         exit("features must be calculated and inside the safe_scores")
#     safe_enriched_nodes = safe_summary['enriched_nodes']
#     safe_enriched_score = safe_summary['enriched_score']
#
#     # extract enriched nodes by safe_summary and take common nodes with intersection
#     enriched_nodes = safe_enriched_nodes[fea1], safe_enriched_nodes[fea2]
#     common_ids = set(enriched_nodes[0]).intersection(set(enriched_nodes[1]))
#
#     def enrich_val(fea):
#         if not common_ids:
#             return 0
#         else:
#             return np.sum([safe_scores[fea][_] for _ in common_ids]) / safe_enriched_score[fea]
#
#     # If common_ids is empty, then output 0 else calculate the ratio of scores of these common nodes in all enriched nodes.
#     coenrich_score = enrich_val(fea1) * enrich_val(fea2)
#     return coenrich_score
#
#
# def coenrich(graph, safe_scores, meta_data, n_iter_value, p_values=0.01):
#     # get detail summary from get_SAFE_summary
#     safe_summary = get_SAFE_summary(graph=graph, meta_data=meta_data, safe_scores=safe_scores,
#                                     n_iter_value=n_iter_value, p_value=p_values, _output_details=True)
#     overall_coenrich = {}
#     n_feas = len(safe_scores.keys())
#     # iterative all fea1,fea2 without repeat.
#     for fea1, fea2 in tqdm.tqdm(itertools.combinations(safe_scores.keys(), 2), total=(n_feas ** 2 - n_feas) / 2):
#         overall_coenrich[(fea1, fea2)] = _pair_enrich(safe_scores, safe_summary, fea1, fea2)
#     graph_coenrich = {}
#     graph_coenrich['edges'] = [k for k, v in overall_coenrich.items() if v != 0]
#     graph_coenrich['edge_weights'] = dict([(k, v) for k, v in overall_coenrich.items() if v != 0])
#     return graph_coenrich


def coenrich_v2(graph, safe_scores):

    nodes = graph['nodes']
    overall_coenrich = {}
    n_feas = len(safe_scores.keys())
    # iterative all fea1,fea2 without repeat.
    for fea1, fea2 in tqdm(itertools.combinations(safe_scores.keys(), 2), total=(n_feas ** 2 - n_feas) / 2):
        if sum(list(safe_scores[fea1].values())) != 0 or sum(list(safe_scores[fea2].values())) != 0:
            _fea1_vals = [safe_scores[fea1][_] for _ in nodes]
            _fea2_vals = [safe_scores[fea2][_] for _ in nodes]

            fea1_vals = [_fea1_vals[idx] for idx in range(len(nodes))]
            fea2_vals = [_fea2_vals[idx] for idx in range(len(nodes))]
            p_test = pearsonr(fea1_vals,
                              fea2_vals)
            overall_coenrich[(fea1, fea2)] = p_test

    graph_coenrich = {}
    graph_coenrich['edges'] = [k for k, v in overall_coenrich.items()]
    graph_coenrich['edge_coeffient'] = dict([(k, v[0]) for k, v in overall_coenrich.items()])
    graph_coenrich['edge_weights'] = dict([(k, v[1]) for k, v in overall_coenrich.items()])
    graph_coenrich['edge_adj_weights(fdr)'] = dict([(k, v) for k, v in zip(overall_coenrich.keys(),
                                                                           fdrcorrection([_[1] for _ in overall_coenrich.values()])[1])])
    return graph_coenrich