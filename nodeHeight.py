#!/usr/bin/python

import optparse
import snap
import bulkwiki2snap


def inNodeIteration(node, dictionary, G):
	""" Recursive function that gets the height of each node in the graph and 
		puts that height as the node's value in the input dictionary
	"""
	maxValue = 0
	for N in node.GetOutEdges():
		if N in dictionary: # If the parent node is already in the dictionary, add 1 to it for current node height
			currentValue = 1 + dictionary[N]
		else:
			currentValue = 1 + inNodeIteration(G.GetNI(N), dictionary, G) # Otherwise recursively go through the graph
		if currentValue > maxValue: 
			maxValue = currentValue
	dictionary[node.GetId()] = maxValue # Store this maxValue of height in the dictionary
	return maxValue


def getHeights(edgeList):
	""" Writes a tab-separated file with the nodes and their heights from this dictionary
	"""

	G = snap.LoadEdgeList(snap.PNGraph, edgeList, 0, 1) # Create a snap PNGraph

	# Open the output file and write the header
	outFile = open("Heights_" + edgeList, "w")
	outFile.write("# Node heights of graph: " + edgeList + "\n")
	outFile.write("# Save as tab-separated list of nodes and their heights\n")
	outFile.write("# Node   Height\n")

	degreeDict = {} # Create an empty dictionary that will hold all the nodes and their heights

	for NI in G.Nodes():
		if NI.GetInDeg() == 0: # Call the recursive function starting at each of the leaves
			inNodeIteration(NI, degreeDict, G) 

	for node in degreeDict: # Write the node and its height into the file
		outFile.write(str(node) + "\t" + str(degreeDict[node]) + "\n")
	outFile.close()
	return degreeDict


def parse_args():
	"""parse_args parses sys.argv for getHeights."""
	# Help Menu
	parser = optparse.OptionParser(usage='%prog [options] title')

	(opts, args) = parser.parse_args()

	# Parser Errors
	if len(args) != 1:
		parser.error('incorrect number of arguments')

	bulkwiki2snap.wiki2snap(args[0]) # Create an edge list file to run getHeights on
	getHeights("edgelists/" + args[0].replace(" ", "_") + ".txt")


if __name__ == '__main__':
	parse_args()
	
