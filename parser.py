#!/usr/bin/python
import optparse
import os
import urllib2
from newPatch import PatchSet, PatchModel

WIKI = 'http://en.wikipedia.org/'

def wiki2snap(title, remove=True):
    """wiki2snap converts a Wikipedia page history to an edge-list."""
    downloadWiki(title)
    return history2snap(title, remove)


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


def history2snap(title, remove=True):
    """
        Converts a Wikipedia page, title, to an edge-list
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
            content=content.split()
            ps = PatchSet.psdiff(pid, prev, content)

            pid+=len(ps.patches)
            for p in ps.patches:
                depends = model.apply_patch(p) #list of out-edges from rev
                for d_pid in depends:
                    graphFile.write( str(p.pid) + "\t" + str(d_pid) + "\n")
            
            prev = content
            compare = False
            getid = True

        
    historyFile.close()
    graphFile.close()
    
    return model.model, content


def parse_args():
    """parse_args parses sys.argv for wiki2snap."""
    # Help Menu
    parser = optparse.OptionParser(usage='%prog [options] title')
    parser.add_option('-r', '--remove',
                      action='store_false', dest='remove', default=True,
                      help='remove mass deletions')

    (opts, args) = parser.parse_args()

    # Parser Errors
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    wiki2snap(args[0], remove=opts.remove)


if __name__ == '__main__':
    parse_args()
