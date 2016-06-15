#!/usr/bin/python

import snap
import optparse

def colorPR(edgeList, dot, graphName):
	"""
	"""
	PRgraph = snap.LoadEdgeList(snap.PNGraph, edgeList, 0, 1)
	PRhash = snap.TIntFltH()
	snap.GetPageRank(PRgraph, PRhash)

	oldGraph = open(dot, "r")
	colorGraph = open(graphName, "w")

	colorGraph.write(oldGraph.readline())

	for node in PRhash:
		prev = oldGraph.readline()
		i=0
		while True:
			if prev[i] == "[":
				i+=1
				break
			else:
				i+=1
		colorGraph.write(prev[0:i] + "style=\"filled\", fillcolor=\"yellow\", " + prev[i:])

	for line in oldGraph:
		colorGraph.write(line)

	oldGraph.close()
	colorGraph.close()



def parse_args():
    """parse_args parses sys.argv for colorPR."""
    parser = optparse.OptionParser(usage='%prog [options] title')
    (opts, args) = parser.parse_args()

    colorPR(args[0], args[1], args[2])


if __name__ == '__main__':
    parse_args()