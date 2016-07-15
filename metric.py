#!/usr/bin/python

import argparse
import networkx as nx
import timestamp as ts
import wiki2graph as w2g
import metric2color as m2c

def getAllHeights(graph):
    """
        Returns a dictionary of the vertices and their weighted heights 
            from the first vertex
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


def getHeight(graph, startDate):
    """
        Returns a dictionary of the vertices and their weighted heights 
            from the first vertices at or after startDate.
    """
    startDate=ts.string2date(startDate)
    nodeList = nx.topological_sort(graph, reverse = True)
    heightDict = {}
    for node in nodeList:
        height = 0
        for (src, dst, dist) in graph.out_edges_iter(node, data='dist'):
            if type(dst) != int:
                intdst = int(dst.decode("utf-8"))
                intsrc = int(src.decode("utf-8"))
                date=graph.node[intsrc]['time']
                date=ts.ts2date(date)
                if date<startDate:
                    height=0
                else:
                    prob = graph.edge[src][dst]['prob'] 
                    height += (heightDict[intdst] + dist)*prob
            else:
                date=graph.node[src]['time']
                date=ts.ts2date(date)
                if date < startDate:
                    height=0
                else:
                    prob=graph.edge[src][dst]['prob']
                    height += (heightDict[dst] + dist)*prob 

        if type(node)!=int:
            node = int(node.decode("utf-8"))
        heightDict[node]= height

    return heightDict


def wiki2color(title, remove, new, allrevs, startDate, metricName):
    """
    """
    (graph, content, model) = w2g.wiki2graph(title, remove, new)
    if allrevs:
        metricDict=getAllHeights(graph)
    else:
        metricDict=getHeight(graph, startDate)
    m2c.metric2color(title, remove, metricName, metricDict)


def parse_args():
    """parse_args parses sys.argv for wiki2color."""
    
    parser = argparse.ArgumentParser(usage='%prog [options] title')

    parser.add_argument('title', nargs=1)
    parser.add_argument('-r', '--remove',
                      action='store_true', dest='remove', default=False,
                      help='remove mass deletions')
    parser.add_argument('-n', '--new',
                      action='store_true', dest='new', default=False,
                      help='reapply model even if cached')
    parser.add_argument('-a', '--all',
                      action='store_true', dest='allrevs', default=False,
                      help='include all revisions')
    parser.add_argument('-s', '--start',
                      dest='start', nargs=1, default='1-1-2001',
                      help='start date for height calculation')
    parser.add_argument('metricName', nargs=1)

    n=parser.parse_args()

    wiki2color(n.title[0], n.remove, n.new, n.allrevs, n.start[0], n.metricName[0])


if __name__ == '__main__':
    parse_args()
