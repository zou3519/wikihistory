#!/usr/bin/python

import networkx as nx
import wiki2graph

def getHeight(graph):
    """ Returns a dictionary of the vertices and their weighted heights from the first vertex
    """     
    nodeList = nx.topological_sort(graph, reverse = True)
    heightDict = {}
    for node in nodeList:
        height = 0
        outDeg = graph.out_degree(node)
        for (src, dst, weight) in graph.out_edges_iter(node, data='weight'):
            if type(dst) != int:
                intdst = int(dst.decode("utf-8"))
                height += heightDict[intdst] + weight
            else:
                height += heightDict[dst] + weight 
        if outDeg>1:
            height=float(height)/outDeg
        if type(node)!=int:
            node = int(node.decode("utf-8"))
        heightDict[node]= height
    return heightDict
