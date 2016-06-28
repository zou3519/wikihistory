#!/usr/bin/python
import optparse
import os
import urllib2
from newPatch import PatchSet, PatchModel

WIKI = 'http://en.wikipedia.org/'

#def wiki2snap(title, remove=True):
#    """wiki2snap converts a WikiIter-able page history to an edge-list."""
#    if not os.path.isdir('edgelists'):
#        os.mkdir('edgelists')


def downloadWiki(title):
    """
        If not in already downloaded,
        download revision history and save to full_histories

        Returns the name of the full history file
    """
    print "Downloading . . ."

    if not os.path.isdir('full_histories'):
        os.mkdir('full_histories')

    api = WIKI+ 'w/index.php?title=Special:Export&pages=' + \
                    title.replace(' ', '+')+'&history&action=submit'
    cachefile = os.path.join('full_histories', title.replace(" ", "_"))
    
    if not (os.path.isfile(cachefile)):
        page = urllib2.urlopen(api)
        file = open(cachefile, 'w')
        for line in page:
            file.write(line)
        file.close()



def getRemlist(fileName):
    """
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


def history2snap(title, remove=True):
    """
    """
    if remove:
        remList=getRemlist("full_histories/"+ title.replace(" ", "_"))

    # Set up snap file
    if not os.path.isdir('edgelists'):
        os.mkdir('edgelists')

    graphFile = open("edgelists/" + title.replace(" ", "_") + ".txt", "w")
    graphFile.write("# Directed graph: " + title + ".txt\n")
    graphFile.write("# Save as tab-separated list of edges\n")
    graphFile.write("# FromNodeId   ToNodeId\n")

    print "Applying model . . ."

    model = PatchModel()
    prev = []
    pid=0
    
    username=False
    useid=True
    compare = False
    writeText=False
    
    historyFile=open("full_histories/"+ title.replace(" ", "_"), "r")

    for line in historyFile:
        line=line.strip()

        # Gets content
        if useid:
            if line[:5] == "<text":
                writeText=True
                content= ""
                line = line.split('">')
                line = line[1]
            if writeText:
                if line[:-7] == "</text>":
                    content+= line[:-7]
                    writeText=False
                    compare = True
                else:
                    content+=line
        
        # Apply to the PatchModel and write dependencies to graph.
        if compare:
            content=content.split()
            ps = PatchSet.psdiff(pid, prev, content)

            pid+=len(ps.patches)
            for p in ps.patches:
                depends = model.apply_patch(p) #list of out-edges from rev
                for d_pid in depends:
                    graphFile.write( str(p.pid) + "\t" + str(d_pid) + "\n")
            
            prev = content

        # Sets whether to use content based on id and remList
        if remove:
            if not username and line[:4] == "<id>":
                rvid = line[4:-5]
                if rvid in remList:
                    useid=False
                    remList.remove(rvid)
                else:
                    useid=True

            if line[:10] == "<username>":
                username=True
            else:
                username=False


    historyFile.close()
    graphFile.close()
    print model.model
    return model.model, content


downloadWiki("Mesostigma")
history2snap("Mesostigma", True)