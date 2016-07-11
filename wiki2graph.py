#!/usr/bin/python

# Contains all function that involve the full Wikipedia history
#    and forming the model/graph

import argparse
import os
import urllib2
import networkx as nx

from newPatch import PatchSet, PatchModel

WIKI = 'http://en.wikipedia.org/'

def downloadHistory(title):
    """
        Downloads the full revision history of the Wikipedia page, title
            and saves to full_histories
    """
    print "Downloading . . ."

    # Make directory
    if not os.path.isdir('full_histories'):
        os.mkdir('full_histories')

    api = WIKI+ 'w/index.php?title=Special:Export&pages=' + \
                    title.replace(' ', '+')+'&history&action=submit'
    cachefile = os.path.join('full_histories', title.replace(" ", "_"))
    
    # Download and save history
    page = urllib2.urlopen(api)
    file = open(cachefile, 'w')
    for line in page:
        file.write(line)
    file.close()

def filterContent(line):
    """
    """
    cleanLine=""
    write=True
    for word in line.split():
        if write and "&lt;ref&gt;" in word:
            i=word.index("&lt;ref&gt;")
            cleanline+=word[:i]+" "
            write=False
        if not write and "&lt;/ref&gt;":
            i=word.index("&lt;ref&gt;")
            cleanline+=word[:i]+" "
            write=True

    return cleanLine


def applyModel(title, remove):
    """
        Applies PatchModel to the history for Wikipedia page, title.
        Returns the full history tranformed into a graph according to the model,
            the PatchModel, and the most recent content.
    """

    # Make folders for model, graph, and content files
    if not os.path.isdir('edgelists'):
        os.mkdir('edgelists')
    if not os.path.isdir('models'):
        os.mkdir('models')
    if not os.path.isdir('content'):
        os.mkdir('content')

    # Get the list of vertices to remove
    if remove:
        remList = getRemlist('full_histories/'+title.replace(" ", "_"))

    print "Applying model . . ."

    model = PatchModel()
    prev = []
    pid=0
    
    getid = True # can read id from doc
    useid= False   # have an id ready to use
    compare = False  # ready to compare content
    writeText= False  # adding to current content
    
    historyFile=open("full_histories/"+ title.replace(" ", "_"), "r")

    line = historyFile.readline().strip()
    while line[:4] != "<id>":
        line=historyFile.readline().strip()

    for line in historyFile:
        line=line.strip()

         # Gets the next valid revision id
        if getid:
            if line[:4] == "<id>":
                rvid = line[4:-5]
                if remove and rvid in  remList: 
                    remList.remove(rvid)
                else:
                    useid=True
                    getid=False

        # Have an id ready to use, looking for start of content
        if useid:
            if line[:5] == "<text":
                content= ""
                line = line.split('">')
                if len(line) == 1:
                    line += [""]
                line = line[1]+"\n"
                useid=False
                writeText=True
        
        # Have reached start if content, looking for end
        if writeText:
            if line[-7:] == "</text>":
                content+=line[:-7]
                writeText=False
                compare = True
            else:
                content+=line+"\n"
        
        # Have text ready to compare. 
        # Apply to the PatchModel and write dependencies to graph.
        if compare:
            contentList=content.split()
            ps = PatchSet.psdiff(pid, prev, contentList)
            pid+=len(ps.patches)
            for p in ps.patches:
                model.apply_patch(p) #list of out-edges from rev
            
            prev = contentList
            compare = False
            getid = True

        
    historyFile.close()

    if remove:
        cachefile = title.replace(" ", "_")+'_rem.txt'
    else:
        cachefile = title.replace(" ", "_")+'.txt'

    # Writes graph to file
    nx.write_weighted_edgelist(model.graph, "edgelists/"+cachefile)
        
    # Write model to file
    modelFile = open("models/"+ cachefile, "w")
    line = ""
    for patch in model.model:
        line+= str(patch[0])+' '+str(patch[1])+'\n'
    modelFile.write(line)
    modelFile.close()

    # Write content to file
    contentFile = open("content/"+ cachefile, "w")
    contentFile.write(content)
    contentFile.close()
    
    return model.graph, content, model.model




def getRemlist(filename):
    """
        Gets a list of ids of revisions that are bot reverts
        or that were reverted by bots
    """
    print "Removing bot rv."
    file = open(filename, "r")
    
    remList = []
    username=False
    
    for line in file:
        line=line.strip()

        if not username and line[:4] == "<id>":
            rvid = line[4:-5]

        if line[:10] == "<username>":
            username=True
        else:
            username=False

        if line[:10] == "<parentid>":
            parentid=line[10:-11]

        if line[:9]=="<comment>":
            if "BOT - rv" in line:
                remList.append(rvid)
                remList.append(parentid)

    file.close()
    return remList




def readGraph(title, remove):
    """
        Reads a networkx graph from a file for Wikipedia page, title, with
            remove 
    """
    print "Reading graph . . ."
    if remove:
        file = "edgelists/" + title.replace(" ", "_")+'_rem.txt'
    else:
        file = "edgelists/" + title.replace(" ", "_")+'.txt'

    assert os.path.isfile(file), "Graph file does not exist."

    return nx.read_weighted_edgelist(file, create_using=nx.DiGraph())




def readContent(title, remove):
    """
        Reads and returns a string from a file
    """
    print "Reading content . . ."

    if remove:
        file = "content/"+title.replace(" ", "_")+"_rem.txt"
    else:
        file = "content/"+title.replace(" ", "_")+".txt"

    assert os.path.isfile(file), "Content file does not exist."

    contentFile = open(file, "r")
    content = ""
    for line in contentFile:
        content+=line
    contentFile.close()
    return content




def readModel(title, remove):
    """
        Reads and returns a PatchModel from a file
    """
    print "Reading model . . ."
    if remove:
        file = "models/"+title.replace(" ", "_")+"_rem.txt"
    else:
        file = "models/"+title.replace(" ", "_")+".txt"

    assert os.path.isfile(file), "Model file does not exist."

    modelFile = open(file, "r")
    model=[]

    # Read model
    for line in modelFile:
        line=line.split()
        model.append((int(line[0]), int(line[1])))
    modelFile.close()
    return model




def wiki2graph(title, remove, new):
    """
        Returns a networkx graph, the content of the latest revision, and the 
            PatchModel for Wikipedia page, title.
        Setting remove to True removes bot reverses and vandalism from the data.
        Setting new to True applies the model whether or not it is cached
    """
    if remove:
        file = title.replace(" ", "_")+"_rem.txt"
    else:
        file = title.replace(" ", "_")+".txt"

    # Check if files exist to avoid reapplying model
    if not new and \
        os.path.isdir('edgelists') and os.path.isfile("edgelists/"+file) and \
        os.path.isdir('content') and os.path.isfile("content/"+file) and \
        os.path.isdir('edgelists') and os.path.isfile("models/"+file):

        graph = readGraph(title, remove)
        content = readContent(title, remove)
        model = readModel(title, remove)

    # Apply model. Download full history if necessary
    else:
        file = title.replace(" ", "_")
        if not os.path.isdir('full_histories') or not os.path.isfile("full_histories/"+file):
            downloadHistory(title)
        (graph, content, model) = applyModel(title, remove)

    return graph, content, model





def parse_args():
    """parse_args parses sys.argv for wiki2graph."""
    # Help Menu
    parser = argparse.ArgumentParser(usage='%prog [options] title')
    parser.add_argument('title', nargs=1)
    parser.add_argument('-r', '--remove',
                      action='store_true', dest='remove', default=False,
                      help='remove mass deletions')
    parser.add_argument('-n', '--new',
                      action='store_true', dest='new', default=False,
                      help='reapply model even if cached')

    n=parser.parse_args()

    wiki2graph(n.title[0], n.remove, n.new)


if __name__ == '__main__':
    parse_args()
