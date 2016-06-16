#!/usr/bin/python
import snap
import optparse

from patch import PatchSet, PatchModel
from wikiiter import WikiIter

WIKI = 'http://en.wikipedia.org/'

# Example call: ./wiki2colorPR.py "Mesostigma" "Mesostigma"

def snap2colorPR(graphName, numNodes):
    """
        Converts a snapGraph, graphName.txt, to a dot graph, graphName.dot,
        colored based on the PageRank of the node
    """
    # Get PRs
    PRgraph = snap.LoadEdgeList(snap.PNGraph, graphName + ".txt", 0, 1)
    PRhash = snap.TIntFltH()
    snap.GetPageRank(PRgraph, PRhash)

    # Set up graph files
    snapGraph = open(graphName+".txt", "r")
    colorGraph = open(graphName+".dot", "w")
    colorGraph.write("digraph " + graphName + " { rankdir=\"BT\";\n")

    # Get to start of edgelist in snapGraph
    for i in range(3):
        snapGraph.readline()
    
    # Adds nodes with colors to colorGraph
    for Id in PRhash:

        nodePR = PRhash[Id]
        scale = 1.0/numNodes

        if nodePR > scale/0.2:
            color = "blue4"
        elif nodePR > scale/0.4:
            color = "navy"
        elif nodePR > scale/0.6:
            color = "royalblue4"
        elif nodePR > scale/0.8:
            color = "steelblue"
        elif nodePR > scale:
            color = "skyblue"
        elif nodePR > scale/1.2:
            color = "turquoise"
        elif nodePR > scale/1.4:
            color = "darkseagreen1"
        elif nodePR > scale/1.6:
            color = "lemonchiffon"
        elif nodePR > scale/2:
            color = "beige"
        else:
            color = "white"
        colorGraph.write(str(Id)+" [style=\"filled\", fillcolor="+color+", label="+str(Id)+"]\n")

    # Adds edges to colorGraph
    for line in snapGraph:
        (src, dst) = line.split()
        colorGraph.write(src+" -> "+dst+" [color=\"black\", fontcolor=\"black\", style=\"bold\"]\n")
    
    # end file
    colorGraph.write("}\n")

    snapGraph.close()
    colorGraph.close()



def wiki2snap(title, graphName):
    """
    	Converts wikipedia page, title, to an edge-list file, graphName.txt
    	Calls snap2color
    """
    witer = WikiIter(WIKI, title, rvcontinue=0)
    model = PatchModel()
    prev = []

    # Set up edge-list file
    graphFile = open(graphName + ".txt", "w")
    graphFile.write("# Directed graph: " + graphName + ".txt\n")
    graphFile.write("# Save as tab-separated list of edges\n")
    graphFile.write("# FromNodeId   ToNodeId\n")
    
    rev = witer.next()
    node = 0   

    while rev is not None:

        # psdiff against the previous revision.
        (revid, comment, content) = rev
        content = content.split()
        ps = PatchSet.psdiff(revid, prev, content)

        # Apply to the PatchModel and write edges to graph.
        outNodeList = model.apply_patchset(ps) 
        for outNode in outNodeList:
            graphFile.write( revid + "  " + outNode + "\n")
            
        prev = content

        node += 1
        rev = witer.next()

    graphFile.close()
    snap2colorPR(graphName, node)


def parse_args():
    """parse_args parses sys.argv and calls wiki2snap."""
    parser = optparse.OptionParser(usage='%prog [options] title')
    (opts, args) = parser.parse_args()

    wiki2snap(args[0], args[1])

if __name__ == '__main__':
    parse_args()