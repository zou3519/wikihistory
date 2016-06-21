#!/usr/bin/python

import optparse
import snap


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
	edges = open(edgeList, "r")
	G = snap.LoadEdgeList(snap.PNGraph, edgeList, 0, 1)

	leafList = []
	degreeDict = {}

	for NI in G.Nodes():
		if NI.GetInDeg() == 0:
			leafList.append(NI.GetId())
			inNodeIteration(NI, degreeDict, G)
	return degreeDict




getHeights("Pradeep_Kumar_Kapur.txt")