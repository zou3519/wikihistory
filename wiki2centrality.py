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

    percentLen = int(length*0.01)

    colors = {}

    # Top 1%
    for i in range(percentLen):
        colors[a[i][1]]="darkred"
    # 1-5
    for i in range(percentLen, percentLen*5):
        colors[a[i][1]]="red"
    # 5-10
    for i in range(percentLen*5, percentLen*10):
        colors[a[i][1]]="mediumred"
    # 10-15
    for i in range(percentLen*10, percentLen*15):
        colors[a[i][1]]="lightred"
    # 15-25
    for i in range(percentLen*15, percentLen*25):
        colors[a[i][1]]="pink"
    for i in range(percentLen*25,length):
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
    colorFile.write(".white {\n\tbackground-color: white;\n\tcolor: black;\n}\n")
    colorFile.write(".pink {\n\tbackground-color: #ffcccc;\n\tcolor: black;\n}\n")
    colorFile.write(".lightred {\n\tbackground-color: #ff9999;\n\tcolor: black;\n}\n")
    colorFile.write(".mediumred {\n\tbackground-color: #ff4d4d;\n\tcolor: black;\n}\n")
    colorFile.write(".red {\n\tbackground-color: #cc0000;\n\tcolor: black;\n}\n")
    colorFile.write(".darkred {\n\tbackground-color: #990000;\n\tcolor: blacj=k;}\n")
    colorFile.write("</style>\n</head>\n")

    # Write content
    colorFile.write("<body>\n")
    
    content=content.splitlines()
    content = [line.split() for line in content]

    pos=0
    dif = model[pos+1][0] - model[pos][0]
    color="white"
    
    for line in content:
        current = "<p><span class="+color+">"
        for i in range(len(line)):
            if dif == 0:
                while dif==0:
                    pos+=1
                    color=colors[model[pos][1]]
                    dif = model[pos+1][0] - model[pos][0]
                current+="</span><span class="+color+">"

            current+=line[i]+ " "
            dif-=1
        current+="</span></p>\n"
        colorFile.write(current)

    colorFile.write("</body>\n</html>")
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
