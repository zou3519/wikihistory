#!/usr/bin/python

import optparse
import os
import wiki2graph as w2g
import metric

# Assumes the existence of a dictionary from an applied metric,
#   a content file, and a model file

def colorPercentile(model, metricDict):
    """
        Assigns edit ids in model to colors by percentile based on
            metricDict. Returns a dictionary of colors.
    """
    print "Assigning colors . . ."
    
    # Sort by decreasing scores
    a=[(metricDict[x[1]], x[1]) for x in model]
    s=set(a)
    a=sorted(list(s), reverse=True)

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
    
    return colors



    
def writeColors(title, remove, metricName, model, content, colors):
    """
    """
    print "Writing heat map . . ."
    # Write style sheet

    if not os.path.isdir('heatmaps'):
        os.mkdir('heatmaps')
    
    if remove:
        colorFile = open("heatmaps/"+(metricName+"_"+title).replace(" ", "_")+"_rem.html", "w")
    else:
        colorFile = open("heatmaps/"+(metricName+"_"+title).replace(" ", "_")+".html", "w")

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

    
    content=content.split("\n")
    content=[line.split() for line in content]

    pos=0
    dif = model[pos][0]
    color="white"
    
    for line in content:
        current = "<p><span class="+color+">"
        for i in range(len(line)):
            if dif == 0:
                while dif==0:
                    pos+=1
                    color=colors[model[pos][1]]
                    dif = model[pos][0] - model[pos-1][0]
                current+="</span><span class="+color+">"

            current+=line[i]+ " "
            dif-=1
        current+="</span></p>\n"
        colorFile.write(current)

    colorFile.write("</body>\n</html>")
    colorFile.close()




def metric2color(title, remove, metricName, metricDict):
    """
    """
    content = w2g.readContent(title, remove)
    model = w2g.readModel(title, remove)
    colors=colorPercentile(model, metricDict)
    writeColors(title, remove, metricName, model, content, colors)



def parse_args():
    """parse_args parses sys.argv for wiki2graph."""
    # Help Menu
    parser = optparse.OptionParser(usage='%prog [options] title')
    parser.add_option('-r', '--remove',
                      action='store_true', dest='remove', default=False,
                      help='remove mass deletions')
    parser.add_option('-n', '--new',
                      action='store_true', dest='new', default=False,
                      help='reapply model even if cached')
    parser.add_option('-m', '--metric',
                      type='str', dest='mtype', default='height',
                      help='name of metric: height, closeness, out_degree, betweenness',
                      metavar='MTYPE')

    (opts, args) = parser.parse_args()

    # Parser Errors
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    (graph, content, model) = w2g.wiki2graph(args[0], remove=opts.remove, new=opts.new)
    heights = metric.getHeight(graph)
    metric2color(args[0], remove = opts.remove, metricName = "height", metricDict = heights)

    # n=parser.parse_args()

    # wiki2graph(n.title[0], n.remove, n.new)

    # (graph, content, model) = w2g.wiki2graph(n.title[0], n.remove, n.new)
    # heights=metric.heights(graph)
    # metric2color(n.title[0], n.remove, "height", heights)


if __name__ == '__main__':
    parse_args()

