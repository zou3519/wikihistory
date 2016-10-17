#!/usr/bin/python

import argparse
import math
import networkx as nx
import timestamp as ts
import wiki2graph as w2g
import metric2color as m2c

# in minutes
MONTH = 43200
YEAR = 525600


def tHeight(graph):
    """
        Returns a dictionary of the vertices and their weighted heights 
            from the first vertices at or after startDate.
    """
    nodeList = nx.topological_sort(graph, reverse=True)
    heightDict = {}
    stime = graph.node[0]['time']
    # Might need to redefine end time. Really should be date of download.
    etime = graph.node[graph.nodes()[-1]]['time']
    #T=ts.time_diff(stime, etime)

    for node in nodeList:
        height = 0
        for (src, dst, prob) in graph.out_edges_iter(node, data='prob'):
            if type(dst) != int:
                dst = int(dst.decode("utf-8"))
                src = int(src.decode("utf-8"))
            date = graph.node[src]['time']
            #t=ts.time_diff(date, etime)/T
            scale = sigmoid(date, etime)
            height += (heightDict[dst] + scale *
                       graph.edge[src][dst]['dist']) * prob

        if type(node) != int:
            node = int(node.decode("utf-8"))
        heightDict[node] = height

    return heightDict


def sigmoid(date, etime):
    """
    """
    lowpercent = 0.01
    diff = ts.time_diff(date, etime)
    if diff < MONTH:
        s = 1.0
    elif diff < YEAR:
        s = 1 - float(diff - MONTH) / (YEAR - MONTH)
        if s < lowpercent:
            s = lowpercent
    else:
        s = lowpercent
    return s
    # et=math.exp(15*(0.5-t))
    # return 1.0/(1+et)


def getAllHeights(graph):
    """
        Returns a dictionary of the vertices and their weighted heights 
            from the first vertex
    """
    nodeList = nx.topological_sort(graph, reverse=True)
    heightDict = {}
    for node in nodeList:
        height = 0
        for (src, dst, prob) in graph.out_edges_iter(node, data='prob'):
            if type(dst) != int:
                dst = int(dst.decode("utf-8"))
                src = int(src.decode("utf-8"))
            height += (heightDict[dst] + graph.edge[src][dst]['dist']) * prob

        if type(node) != int:
            node = int(node.decode("utf-8"))
        heightDict[node] = height

    return heightDict


def getHeight(graph, startDate):
    """
        Returns a dictionary of the vertices and their weighted heights 
            from the first vertices at or after startDate.
    """
    startDate = ts.string2date(startDate)
    nodeList = nx.topological_sort(graph, reverse=True)
    heightDict = {}
    for node in nodeList:
        height = 0
        for (src, dst, prob) in graph.out_edges_iter(node, data='prob'):
            if type(dst) != int:
                dst = int(dst.decode("utf-8"))
                src = int(src.decode("utf-8"))
            date = graph.node[src]['time']
            date = ts.ts2date(date)
            if date < startDate:
                height = 0
            else:
                height += (heightDict[dst] +
                           graph.edge[src][dst]['dist']) * prob

        if type(node) != int:
            node = int(node.decode("utf-8"))
        heightDict[node] = height

    return heightDict


def wiki2color(title, remove, new, allrevs, startDate, shade, metricName):
    """
        Produces a heatmap of the metric height over the most recent revision.
    """
    (graph, content, model) = w2g.wiki2graph(title, remove, new)
    if allrevs:
        metricDict = tHeight(graph)
        # metricDict=getAllHeights(graph)
    else:
        metricDict = getHeight(graph, startDate)

    if shade:
        m2c.metric2shades(title, remove, metricName, metricDict)
    else:
        m2c.metric2color(title, remove, metricName, metricDict)


def parse_args():
    """parse_args parses sys.argv for wiki2color."""

    parser = argparse.ArgumentParser(usage='%%prog [options] title')

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
    parser.add_argument('-sh', '--shade',
                        action='store_true', dest='shade', default=False,
                        help='color by score instead of percentile')
    parser.add_argument('metricName', nargs=1)

    n = parser.parse_args()

    wiki2color(n.title[0], n.remove, n.new, n.allrevs,
               n.start[0], n.shade, n.metricName[0])


if __name__ == '__main__':
    parse_args()
