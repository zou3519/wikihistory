#!/usr/bin/python

# Contains all function that involve the full Wikipedia history
#    and forming the model/graph

import optparse
import os
import urllib2

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

    


def applyModel(title, remove):
    """
        Applies PatchModel to the history for Wikipedia page, title.
        Returns the full history tranformed into a graph according to the model,
            the PatchModel, and the most recent content.
    """

    print "Applying model . . ."

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
                apply_patch(p) #list of out-edges from rev
            
            prev = contentList
            compare = False
            getid = True

        
    historyFile.close()

    # Writes graph to file
    if remove:
        nx.write_edgelist(model.graph, "edgelists/"+title.replace(" ", "_")+'_rem.txt')
    else:
        nx.write_edgelist(model.graph, "edgelists/"+title.replace(" ", "_")+'.txt')
        
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




def getRemlist(title):
    """
        Gets a list of ids of revisions that are bot reverts
        or that were reverted by bots
    """
    print "Removing bot rv."
    file = open(fileName, "r")
    
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

    return nx.read_edgelist(file)




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

    # Handle None id
    line=modelFile.readline()
    line=line.split()
    model.append((int(line[0]), None))

    # Read rest of model
    for line in modelFile:
        line=line.split()
        model.append((int(line[0]), int(line[1])))
    modelFile.close()
    return model
