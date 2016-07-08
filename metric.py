#!/usr/bin/python

import networkx as nx

def heights(graph):
    """
    """
    "Calculating heights . . ."
    heightDict= {}
    for N in graph:
        if graph.in_degree(N) == 0:
            getHeight(graph, N, heightDict)
    print heightDict
    return heightDict

def getHeight(graph, node, heightDict):
    """
    """
    height=0
    outDeg = graph.out_degree(node)
    for (src, dst, weight) in graph.out_edges_iter(node, data='weight'):
        if type(dst) != int:
            intdst = int(dst.decode("utf-8"))
            if intdst in heightDict:
                height += heightDict[intdst] + weight
            else:
                height+= getHeight(graph, dst, heightDict) + weight
        else:
            if dst in heightDict:
                height += heightDict[dst] + weight
            else:
                height+= getHeight(graph, dst, heightDict) + weight
    if outDeg>1:
        height=float(height)/outDeg
    if type(node)!=int:
        node = int(node.decode("utf-8"))
    heightDict[node]= height
    return height



