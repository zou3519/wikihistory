#!/usr/bin/python
import nodeHeight
import optparse
import wiki2snap



def colorRevisions(title, model, content, heightDict):
    """
    """
    colorFile = open(title+".html", "w")

    # Write style sheet
    colorFile.write("<!DOCTYPE html>\n<html>\n<head>\n<style/>\n")
    colorFile.write(".white {\n\tbackground-color: white;\n}\n")
    colorFile.write(".aquamarine {\n\tbackground-color: aquamarine;\n}\n")
    colorFile.write(".cyan {\n\tbackground-color: cyan;\n}\n")
    colorFile.write(".royalblue {\n\tbackground-color: royalblue;\n}\n")
    colorFile.write(".blue {\n\tbackground-color: blue;\ncolor: white;\n}\n")
    colorFile.write(".darkblue {\n\tbackground-color: darkblue;\ncolor: white}\n")
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
        owner = model[i][1]
        colorClass = "white"
        if owner!=None:
            edits = heightDict[owner]
            colorClass = getColor(edits)

        colorFile.write("<span class="+ colorClass+ ">"+line+"</span>\n")

    colorFile.write("</p>\n</body>\n</html>")
    colorFile.close()

def getColor(edits):
    """
    """
    color = "white"
    if edits > 10:
        color = "darkblue"
    elif edits > 8:
        color="blue"
    elif edits > 6:
        color = "royalblue"
    elif edits>4:
        color="cyan"
    elif edits>2:
        color="aquamarine"
    return color


    


def parse_args():
    """parse_args parses sys.argv for prettyColors."""
    # Help Menu
    parser = optparse.OptionParser(usage='%prog [options] title')
    
    (opts, args) = parser.parse_args()

    # Parser Errors
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    title=args[0]
    (model, content) = wiki2snap.wiki2snap(title)
    heightDict=nodeHeight.getHeights(title.replace(" ", "_") + ".txt")
    colorRevisions(title.replace(" ", "_"), model, content, heightDict)
    


if __name__ == '__main__':
    parse_args()