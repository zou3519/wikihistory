#!/usr/bin/python

import argparse
import networkx as nx
import timestamp as ts
import wiki2graph as w2g
import metric2color as m2c


def tHeight2(graph):
    """
    """
    stime=graph.node[0]['time']
    etime=graph.node[graph.nodes()[-1]]['time']
    T=ts.time_diff(stime, etime)
    

    nodeList = nx.topological_sort(graph, reverse = True)
    heightDict = {}
    timeDict = {}
    for node in nodeList:
        height = 0
        for (src, dst, prob) in graph.out_edges_iter(node, data='prob'):
            if type(dst) != int:
                dst = int(dst.decode("utf-8"))
                src = int(src.decode("utf-8")) 
            #t=float(ts.time_diff(stime, graph.node[src]['time']))/T
            dist=graph.edge[src][dst]['dist']
            height += (heightDict[dst]+dist)*prob

        if type(node)!=int:
            node = int(node.decode("utf-8"))
        heightDict[node]= height
    for node in heightDict:
        nodeTime = ts.time_diff(graph.node[node], etime)
        newHeight = heightDict[node]/nodeTime
        timeDict[node] = newHeight

    return timeDict


def tHeight(graph):
    """
    """
    stime=graph.node[0]['time']
    etime=graph.node[graph.nodes()[-1]]['time']
    T=ts.time_diff(stime, etime)
    

    nodeList = nx.topological_sort(graph, reverse = True)
    heightDict = {}
    for node in nodeList:
        height = 0
        for (src, dst, prob) in graph.out_edges_iter(node, data='prob'):
            if type(dst) != int:
                dst = int(dst.decode("utf-8"))
                src = int(src.decode("utf-8")) 
            t=ts.time_diff(graph.node[dst]['time'], graph.node[src]['time'])/T
            if t==0:
                t=1
            #t=float(ts.time_diff(stime, graph.node[src]['time']))/T
            dist=graph.edge[src][dst]['dist']
            height += (heightDict[dst]+dist)*prob/t

        if type(node)!=int:
            node = int(node.decode("utf-8"))
        heightDict[node]= height

    return heightDict


def allkHeights(graph):
    """
        Returns a dictionary of the vertices and their damped, weighted
            heights from the first vertex
    """
    heightDict={}
    k=0.75
    nodeList = nx.topological_sort(graph, reverse = True)
    for node in nodeList:
        height=0
        for (src, dst, prob) in graph.out_edges_iter(node, data='prob'):
            if type(dst) != int:
                dst = int(dst.decode("utf-8"))
                src = int(src.decode("utf-8")) 
            height += (k*heightDict[dst]+graph.edge[src][dst]['dist'])*prob
        heightDict[node]= height
    
    return heightDict




def kHeight(graph, startDate):
    """
        Returns a dictionary of the vertices and their damped, weighted heights 
            from the first vertices at or after startDate.
    """
    k=1.0
    startDate=ts.string2date(startDate)
    nodeList = nx.topological_sort(graph, reverse = True)
    heightDict = {}
    for node in nodeList:
        height = 0
        for (src, dst, prob) in graph.out_edges_iter(node, data='prob'):
            if type(dst) != int:
                dst = int(dst.decode("utf-8"))
                src = int(src.decode("utf-8"))
            date=graph.node[src]['time']
            date=ts.ts2date(date)
            if date < startDate:
                height=0
            else:
                height += (k*heightDict[dst]+graph.edge[src][dst]['dist'])*prob 

        if type(node)!=int:
            node = int(node.decode("utf-8"))
        heightDict[node]= height

    return heightDict





def getAllHeights(graph):
    """
        Returns a dictionary of the vertices and their weighted heights 
            from the first vertex
    """     
    nodeList = nx.topological_sort(graph, reverse = True)
    heightDict = {}
    for node in nodeList:
        height = 0
        for (src, dst, prob) in graph.out_edges_iter(node, data='prob'):
            if type(dst) != int:
                dst = int(dst.decode("utf-8"))
                src = int(src.decode("utf-8")) 
            height += (heightDict[dst]+graph.edge[src][dst]['dist'])*prob

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
        for (src, dst, prob) in graph.out_edges_iter(node, data='prob'):
            if type(dst) != int:
                dst = int(dst.decode("utf-8"))
                src = int(src.decode("utf-8"))
            date=graph.node[src]['time']
            date=ts.ts2date(date)
            if date < startDate:
                height=0
            else:
                height += (heightDict[dst]+graph.edge[src][dst]['dist'])*prob 

        if type(node)!=int:
            node = int(node.decode("utf-8"))
        heightDict[node]= height

    return heightDict




def wiki2color(title, remove, new, allrevs, startDate, shade, metricName):
    """
        Produces a heatmap of the metric height over the most recent revision.
    """
    (graph, content, model) = w2g.wiki2graph(title, remove, new)
    #if allrevs:
    #   metricDict=getAllHeights(graph)
    #else:
    #    metricDict=getHeight(graph, startDate)
    #if allrevs:
    #   metricDict=allkHeights(graph)
    #else:
     #   metricDict=kHeight(graph, startDate)
    metricDict=tHeight2(graph)
    if shade:
        m2c.metric2shades(title, remove, metricName, metricDict)
    else:
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
    parser.add_argument('-sh', '--shade',
                      action='store_true', dest='shade', default=False,
                      help='color by score instead of percentile')
    parser.add_argument('metricName', nargs=1)

    n=parser.parse_args()

    wiki2color(n.title[0], n.remove, n.new, n.allrevs, n.start[0], n.shade, n.metricName[0])


if __name__ == '__main__':
    parse_args()
