#!/usr/bin/python

import optparse
import snap
import wiki2snap


def inNodeIteration(node, dictionary, G):
	maxValue = 0
	for N in node.GetOutEdges():
		if N in dictionary:
			currentValue = 1 + dictionary[N]
		else:
			currentValue = 1 + inNodeIteration(G.GetNI(N), dictionary, G)
		if currentValue > maxValue:
			maxValue = currentValue
	dictionary[node.GetId()] = maxValue
	return maxValue


def getHeights(edgeList):
	""" Creates a dictionary with the longest path to each of the nodes in the edgeList"""
	G = snap.LoadEdgeList(snap.PNGraph, edgeList, 0, 1)
	outFile = open("Heights_" + edgeList, "w")
	outFile.write("# Node heights of graph: " + edgeList + "\n")
	outFile.write("# Save as tab-separated list of nodes and their heights\n")
	outFile.write("# Node   Height\n")

	leafList = []
	degreeDict = {}

	for NI in G.Nodes():
		if NI.GetInDeg() == 0:
			leafList.append(NI.GetId())
			inNodeIteration(NI, degreeDict, G)

	for node in degreeDict:
		outFile.write(str(node) + "\t" + str(degreeDict[node]) + "\n")
	outFile.close()
	return degreeDict


def parse_args():
	"""parse_args parses sys.argv for wiki2snap."""
	# Help Menu
	parser = optparse.OptionParser(usage='%prog [options] title')

	(opts, args) = parser.parse_args()

	# Parser Errors
	if len(args) != 1:
		parser.error('incorrect number of arguments')

	wiki2snap.wiki2snap(args[0])
	getHeights(args[0].replace(" ", "_") + ".txt")


if __name__ == '__main__':
	parse_args()
	
