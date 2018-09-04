from __future__ import print_function

import csv
import os

import networkx as nx
import numpy as np
import pandas as pd
import scipy.stats as scs
from sklearn.neighbors import *
from sklearn.preprocessing import MinMaxScaler

from tmap.tda import mapper
from tmap.tda.cover import Cover


def optimize_dbscan_eps(data, threshold=90,dm=None):
    if dm is not None:
        tmp = dm.where(dm != 0, np.inf)
        eps = np.percentile(np.min(tmp,axis=0),threshold)
        return eps
    # using metric='minkowski', p=2 (that is, a euclidean metric)
    tree = KDTree(data, leaf_size=30, metric='minkowski', p=2)
    # the first nearest neighbor is itself, set k=2 to get the second returned
    dist, ind = tree.query(data, k=2)
    # to have a percentage of the 'threshold' of points to have their nearest-neighbor covered
    eps = np.percentile(dist[:, 1], threshold)
    return eps

def optimal_r(X, projected_X, clusterer, mid,overlap,step=1):
    def get_y(r):
        tm = mapper.Mapper(verbose=0)
        cover = Cover(projected_data=MinMaxScaler().fit_transform(projected_X), resolution=r, overlap=0.75)
        graph = tm.map(data=X, cover=cover, clusterer=clusterer)
        if "adj_matrix" not in graph.keys():
            return np.inf
        return abs(scs.skew(graph["adj_matrix"].count()))
    mid_y = get_y(mid)
    mid_y_r = get_y(mid + 1)
    mid_y_l = get_y(mid - 1)
    while 1:
        min_r = sorted(zip([mid_y_l,mid_y,mid_y_r],[mid-1,mid,mid+1]))[0][1]
        if min_r == mid-step:
            mid -= step
            mid_y,mid_y_r = mid_y_l,mid_y
            mid_y_l = get_y(mid)
        elif min_r == mid + step:
            mid += step
            mid_y,mid_y_l = mid_y_r,mid_y
            mid_y_r = get_y(mid)
        else:
            break
    print("suitable resolution is ",mid)
    return mid

def construct_node_data(graph,data):
    nodes = graph['nodes']
    node_data = {k: data.iloc[v, :].mean(axis=0) for k, v in nodes.items()}
    node_data = pd.DataFrame.from_dict(node_data, orient='index')
    return node_data

def get_pos(graph,strength):
    node_keys = graph["node_keys"]
    node_positions = graph["node_positions"]
    G = nx.Graph()
    G.add_nodes_from(graph['nodes'].keys())
    G.add_edges_from(graph['edges'])
    pos = {}
    for i, k in enumerate(node_keys):
        pos.update({int(k): node_positions[i, :2]})
    pos = nx.spring_layout(G, pos=pos, k=strength)
    return pos

## Access inner attribute

def cover_ratio(graph,data):
    nodes = graph['nodes']
    all_samples_in_nodes = [_ for vals in nodes.values() for _ in vals]
    n_all_sampels = data.shape[0]
    n_in_nodes = len(set(all_samples_in_nodes))
    return n_in_nodes/float(n_all_sampels) * 100

## Export data as file

def safe_scores_IO(arg,output_path=None,mode='w'):
    if mode == 'w':
        if not isinstance(arg,pd.DataFrame):
            safe_scores = pd.DataFrame.from_dict(arg,orient='index')
            safe_scores = safe_scores.T
        else:
            safe_scores = arg
        safe_scores.to_csv(output_path,index=True)
    elif mode == 'rd':
        safe_scores = pd.read_csv(arg,index_col=0)
        safe_scores = safe_scores.to_dict()
        return safe_scores
    elif mode == 'r':
        safe_scores = pd.read_csv(arg,index_col=0)
        return safe_scores


def output_graph(graph,filepath,sep='\t'):
    """
    Export graph as a file with sep. The output file should be used with `Cytoscape <http://cytoscape.org/>`_ .

    It should be noticed that it will overwrite the file you provided.

    :param dict graph: Graph output from tda.mapper.map
    :param str filepath:
    :param str sep:
    """
    edges = graph['edges']
    with open(os.path.realpath(filepath),'w') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=sep)
        spamwriter.writerow(['Source', 'Target'])
        for source,target in edges:
            spamwriter.writerow([source,target])

def output_Node_data(graph,filepath,data,features = None,sep='\t',target_by='sample'):
    """
    Export Node data with provided filepath. The output file should be used with `Cytoscape <http://cytoscape.org/>`_ .

    It should be noticed that it will overwrite the file you provided.

    :param dict graph:
    :param str filepath:
    :param np.ndarray/pandas.Dataframe data: with shape [n_samples,n_features] or [n_nodes,n_features]
    :param list features: It could be None and it will use count number as feature names.
    :param str sep:
    :param str target_by: target type of "sample" or "node"
    """
    if target_by not in ['sample','node']:
        exit("target_by should is one of ['sample','node']")
    nodes = graph['nodes']
    node_keys = graph['node_keys']
    if 'columns' in dir(data) and features is None:
        features = list(data.columns)
    elif 'columns' not in dir(data) and features is None:
        features = list(range(data.shape[1]))
    else:
        features = list(features)

    if type(data) != np.ndarray:
        data = np.array(data)

    if target_by == 'sample':
        data = np.array([np.mean(data[nodes[_]],axis=0) for _ in node_keys])
    else:
        pass

    with open(os.path.realpath(filepath),'w') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=sep)
        spamwriter.writerow(['NodeID'] + features)
        for idx,v in enumerate(node_keys):
            spamwriter.writerow([str(v)] + [str(_) for _ in data[idx,:]])

def output_Edge_data(graph,filepath,sep='\t'):
    """
    Export edge data with sep [default=TAB]

    Mainly for the result of tmap.tda.netx.coenrich

    The output file should be used with `Cytoscape <http://cytoscape.org/>`_ .

    :param dict graph: graph output by netx.coenrich
    :param str filepath:
    :param str sep:
    """
    if isinstance(graph,dict):
        if "association_coeffient" in graph.keys() and "associated_pairs" in graph.keys():
            edges = graph["associated_pairs"]
            edge_weights = graph["association_coeffient"]
            with open(os.path.realpath(filepath), 'w') as csvfile:
                spamwriter = csv.writer(csvfile, delimiter=sep)
                spamwriter.writerow(["Edge name","coenrich_score"])
                for node1,node2 in edges:
                    spamwriter.writerow(["%s (interacts with) %s" % (node1,node2),
                                         edge_weights[(node1,node2)]])
        else:
            print("Missing key 'association_coeffient' or 'associated_pairs' in graph")
    else:
        print("graph should be a dictionary")
