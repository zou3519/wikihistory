#!/usr/bin/python
import networkx as nx
import parser
import optparse
import os


def centrality(edgeList, ctype):
    """
    """
    print "centrality start"

    file = open(edgeList, "r")
    graph = nx.read_edgelist(file, comments="#", create_using=nx.DiGraph(), nodetype=int)
    file.close()

    if ctype == "out_degree":
        centrality = nx.out_degree_centrality(graph)
    elif ctype == "betweenness":
        centrality=nx.betweenness_centrality(graph)
    else:
        centrality = nx.closeness_centrality(graph)
    
    return centrality
	
def colorPercentile(model, centrality):
    """
    """
    print "colorPercentile start"
    NUMCOLORS=6

    # Get ids of nodes in model and sort by decreasing centrality
    a=[(centrality[x[1]], x[1]) for x in model if x[1] != None]
    s=set(a)
    a=sorted(list(s), reverse=True)
    print "sorting done"

    # Assign colors to nodes
    length=len(a)
    # scale=length/NUMCOLORS

    percentLen = int(length*0.1)

    colors = {}

    for i in range(percentLen):
        colors[a[i][1]]="darkred"
    for i in range(percentLen, percentLen*2):
        colors[a[i][1]]="red"
    for i in range(percentLen*2, percentLen*3):
        colors[a[i][1]]="mediumred"
    for i in range(percentLen*3, percentLen*4):
        colors[a[i][1]]="lightred"
    for i in range(percentLen*4, percentLen*5):
        colors[a[i][1]]="pink"
    for i in range(percentLen*5,length):
        colors[a[i][1]]="white"
    print "colorPercentile done"
    return colors
	
def writeColors(title, model, content, colors, ctype):
    print "writeColors start"
    # Write style sheet

    if not os.path.isdir('centrality'):
        os.mkdir('centrality')
    
    colorFile = open("centrality/"+(ctype+"_"+title).replace(" ", "_")+".html", "w")

    colorFile.write("<!DOCTYPE html>\n<html>\n<head>\n<style/>\n")
    colorFile.write(".white {\n\tbackground-color: white;\n color: black;\n}\n")
    colorFile.write(".pink {\n\tbackground-color: #ffcccc;\ncolor: black;\n}\n")
    colorFile.write(".lightred {\n\tbackground-color: #ff9999;\ncolor: black;\n}\n")
    colorFile.write(".mediumred {\n\tbackground-color: #ff4d4d;\ncolor: black;\n}\n")
    colorFile.write(".red {\n\tbackground-color: #cc0000;\ncolor: black;\n}\n")
    colorFile.write(".darkred {\n\tbackground-color: #990000;\ncolor: blacj=k;}\n")
    colorFile.write("</style>\n</head>\n")

    # Write content
    colorFile.write("<body>\n<p>\n")
    length = len(model)
    for i in range(length-1):
        # Get text
        start = model[i][0]
        end = model[i+1][0]
        line=""
        for current in content[start:end]:
            line+=current + " "

        # Get color
        revid=model[i][1]
        if revid==None:
        	color="white"
        else:
        	color = colors[model[i][1]]
    	colorFile.write("<span class="+ color+ ">"+line+"</span>\n")

    colorFile.write("</p>\n</body>\n</html>")
    colorFile.close()
    print "writeColors done"

def wiki2centrality(title, remove, ctype):
	"""
	"""
	model,content=parser.wiki2snap(title, remove)
	centralityDict = centrality("edgelists/" + title.replace(" ", "_") + ".txt", ctype)
	colors = colorPercentile(model, centralityDict)
	writeColors(title, model, content, colors, ctype)




def parse_args():
    """parse_args parses sys.argv for wiki2centrality."""
    # Help Menu
    parser = optparse.OptionParser(usage='%prog [options] title')
    parser.add_option('-r', '--remove',
                      action='store_false', dest='remove', default=True,
                      help='remove mass deletions')
    parser.add_option('-c', '--centrality',
                      type='str', dest='ctype', default='closeness',
                      help='type of centrality: closeness, out_degree, betweenness',
                      metavar='CTYPE')

    (opts, args) = parser.parse_args()

    # Parser Errors
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    wiki2centrality(args[0], remove=opts.remove, ctype=opts.ctype)


if __name__ == '__main__':
    parse_args()

