#!/usr/bin/python

import snap
import optparse

def colorPR(edgeList, dot, graphName):
	"""
		Colors a graph so that nodes with a higher PR are darker
		Input: 3 strings: a txt file containing an edgelist, a
			dot file of the same graph, and the name of a new dot file
			for the resulting colored graph 
	"""
	PRgraph = snap.LoadEdgeList(snap.PNGraph, edgeList, 0, 1)
	PRhash = snap.TIntFltH()
	snap.GetPageRank(PRgraph, PRhash)

	N = float(PRgraph.GetNodes())

	oldGraph = open(dot, "r")
	colorGraph = open(graphName, "w")

	colorGraph.write(oldGraph.readline())
	print len(PRhash)
	for line in oldGraph:
		
		(node, info) = line.split(" ",1)
		if info[0] == "-":
			break
		
		node = int(node)
		nodePR = 0.
		try:
			nodePR = PRhash[node]
		except:
			None
		if nodePR > 1/(0.2*N):
			# print node, nodePR
			color = "blue4"
		elif nodePR > 1/(0.3*N):
			color = "navy"
		elif nodePR > 1/(0.4*N):
			color = "royalblue4"
		elif nodePR > 1/(0.5*N):
			color = "steelblue"
		elif nodePR > 1/(0.6*N):
			color = "skyblue"
		elif nodePR > 1/(0.7*N):
			color = "turquoise"
		elif nodePR > 1/(0.8*N):
			color = "darkseagreen1"
		elif nodePR > 1/(0.9*N):
			# print "lemon ", node, nodePR
			color = "lemonchiffon"
		elif nodePR > 1/N:
			# print "beige ", node, nodePR
			color = "beige"
		else:
			color = "white"
		colorGraph.write(str(node) + ' [style=\"filled\", fillcolor=' + color + ',label="' + str(node) + '"]')

	

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