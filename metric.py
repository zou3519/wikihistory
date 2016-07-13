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
        for (src, dst, dist) in graph.out_edges_iter(node, data='dist'):
            if type(dst) != int:
                intdst = int(dst.decode("utf-8"))
                intsrc = int(src.decode("utf-8"))
                prob = graph.edge[src][dst]['prob'] 
                height += (heightDict[intdst] + dist)*prob
            else:
                prob=graph.edge[src][dst]['prob']
                height += (heightDict[dst] + dist)*prob 
    
        if type(node)!=int:
            node = int(node.decode("utf-8"))
        heightDict[node]= height
    return heightDict
