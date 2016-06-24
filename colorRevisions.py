#!/usr/bin/python
import nodeHeight
import optparse
import bulkwiki2snap



def colorRevisions(title, model, content, heightDict):
    """
        Creates a html file containing the most recent version of content, the content
        of the Wikipedia page, title, colored based on the PatchModel, model, and the height
        of each of the nodes, stored in heightDict.

        Darker colors mean more revisions.

    """
    numPatches = len(model)
    totalEdits = 0
    for i in model:
        rev = i[1]
        if rev != None:
            totalEdits+=heightDict[rev]

    colorFile = open(title+".html", "w")

    # Write style sheet
    colorFile.write("<!DOCTYPE html>\n<html>\n<head>\n<style/>\n")
    colorFile.write(".white {\n\tbackground-color: white;\n color: black;\n}\n")
    colorFile.write(".aquamarine {\n\tbackground-color: aquamarine;\ncolor: black;\n}\n")
    colorFile.write(".cyan {\n\tbackground-color: cyan;\ncolor: black;\n}\n")
    colorFile.write(".royalblue {\n\tbackground-color: royalblue;\ncolor: black;\n}\n")
    colorFile.write(".blue {\n\tbackground-color: blue;\ncolor: white;\n}\n")
    colorFile.write(".darkblue {\n\tbackground-color: darkblue;\ncolor: white;}\n")
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
            colorClass = getColor(edits, totalEdits, numPatches)


        colorFile.write("<span class="+ colorClass+ ">"+line+"</span>\n")

    colorFile.write("</p>\n</body>\n</html>")
    colorFile.close()

    

def getColor(edits, totalEdits, numPatches):
    """
        Finds the color class based on the number of edits.
    """
    percent = numPatches*float(edits)/float(totalEdits)

    color = "white"
    if percent > 2.5:
        color = "darkblue"
    elif percent > 2:
        color="blue"
    elif percent > 1.5:
        color = "royalblue"
    elif percent>1.25:
        color="cyan"
    elif percent>1:
        color="aquamarine"
    return color


    


def parse_args():
    """parse_args parses sys.argv for colorRevisions."""
    # Help Menu
    parser = optparse.OptionParser(usage='%prog [options] title')
    
    (opts, args) = parser.parse_args()

    # Parser Errors
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    title=args[0]
    (model, content) = bulkwiki2snap.wiki2snap(title)
    heightDict=nodeHeight.getHeights(title.replace(" ", "_") + ".txt")
    colorRevisions(title.replace(" ", "_"), model, content, heightDict)
    


if __name__ == '__main__':
    parse_args()