#!/usr/bin/python
import optparse
import os
import sys
import libxml2
import urllib2
import xml.etree.ElementTree as ET

from newPatch import PatchSet, PatchModel
from progressbar import ProgressBar

WIKI = 'http://en.wikipedia.org/'
NAMESPACE = '{http://www.mediawiki.org/xml/export-0.10/}'

def wiki2snap(title, remove=True):
    """wiki2snap converts a WikiIter-able page history to an edge-list."""
    if not os.path.isdir('data'):
        os.mkdir('data')

    model = PatchModel()
    prev = []
    prevComment=""
    
    # Set up snap file
    graphFile = open("edgelists/" + title.replace(" ", "_") + ".txt", "w")
    graphFile.write("# Directed graph: " + title + ".txt\n")
    graphFile.write("# Save as tab-separated list of edges\n")
    graphFile.write("# FromNodeId   ToNodeId\n")

    # If not in cache, download revision history and save to full_histories
    api = WIKI+ 'w/index.php?title=Special:Export&pages=' + \
                    title.replace(' ', '+')+'&history&action=submit'
    cachefile = os.path.join('full_histories', title.replace(" ", "_"))

    progress = ProgressBar('Processing "' + title + '"', maximum=None)
    
    if not (os.path.isfile(cachefile)):
        # doc= libxml2.parseDoc(urllib2.urlopen(api).read())
        page = urllib2.urlopen(api)
        file = open(cachefile, 'w')
        for line in page:
            file.write(line)
        # doc.saveTo(file, encoding='UTF-8', format=1)
        file.close()
    
    parser = ET.XMLParser(encoding="utf-8")
    tree=ET.parse(cachefile, parser = parser)
    root=tree.getroot()
    page=tree.find(NAMESPACE+'page')

    remList = []

    if remove:
        for rev in page.iter(NAMESPACE+'revision'):
            parent = rev.find(NAMESPACE+'parentid')
            comment = rev.find(NAMESPACE+'comment')
            revid = rev.find(NAMESPACE+'id')
        
            if parent != None and comment != None and "BOT - rv" in comment.text:
                remList.append(parent.text)
                remList.append(revid.text)
    

    
    pid=0
    
    
    for rev in page.iter(NAMESPACE+'revision'):
        progress.next()
        # psdiff against the previous revision.
        rvid = rev.find(NAMESPACE+'id').text
        if (not remove) or (rvid not in remList):
            comment = rev.find(NAMESPACE+'comment')
            if comment==None:
                comment=""
            else:
                comment=comment.text.encode("utf-8")

            content = rev.find(NAMESPACE+'text').text
            if content==None:
                content=[]
            else:
                content=content.encode("utf-8").split()
        
            ps = PatchSet.psdiff(pid, prev, content)

            # Apply to the PatchModel and write dependencies to graph.
            pid+=len(ps.patches)
            for p in ps.patches:
                depends = model.apply_patch(p) #list of out-edges from rev
                for d_pid in depends:
                    graphFile.write( str(p.pid) + "  " + str(d_pid) + "\n")
            
            prev = content
        else:
            remList.remove(rvid)


    sys.stdout.write(' done.\n')
    sys.stdout.flush()
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
    