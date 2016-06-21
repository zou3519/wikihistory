#!/usr/bin/python
import optparse
import os
import sys

from patch import PatchSet, PatchModel
from progressbar import ProgressBar
from wikiiter import WikiIter


NAME = 'wiki2snap.py'
VERSION = 'v0.1'
WIKI = 'http://en.wikipedia.org/'


def wiki2snap(title, maximum=None, rvcontinue=0, warm=False):
    """wiki2snap converts a WikiIter-able page history to an edge-list."""
    if not os.path.isdir('data'):
        os.mkdir('data')

    witer = WikiIter(WIKI, title, rvcontinue=rvcontinue)
    progress = ProgressBar('Processing "' + title + '"', maximum=maximum)   

    if not warm:
        model = PatchModel()
        prev = []
    
        graphFile = open(title.replace(" ", "_") + ".txt", "w")
        graphFile.write("# Directed graph: " + title + ".txt\n")
        graphFile.write("# Save as tab-separated list of edges\n")
        graphFile.write("# FromNodeId   ToNodeId\n")
    
    rev = witer.next()
    node = 0   
    while rev is not None and (maximum is None or node < maximum):
        progress.next()
        
        if not warm:    
            # psdiff against the previous revision.
            (revid, comment, content) = rev
            content = content.split()
            ps = PatchSet.psdiff(revid, prev, content)

            # Apply to the PatchModel and write dependencies to graph.
            depends = model.apply_patchset(ps) #list of out-edges from rev
            for d_psid in depends:
                graphFile.write( revid + "  " + d_psid + "\n")
            
            prev = content

        node += 1
        rev = witer.next()

    sys.stdout.write(' done.\n')
    sys.stdout.flush()
    graphFile.close()




def parse_args():
    """parse_args parses sys.argv for wiki2snap."""
    # Help Menu
    parser = optparse.OptionParser(usage='%prog [options] title')
    parser.add_option('-m', '--max',
                      type='int', dest='maximum', default=None,
                      help='process at most MAX revisions', metavar='MAX')
    parser.add_option('-s', '--start',
                      type='str', dest='rvcontinue', default='0',
                      help='start from START revid', metavar='START')
    parser.add_option('-w', '--warm',
                      action='store_true', dest='warm', default=False,
                      help='warm the cache without processing')

    (opts, args) = parser.parse_args()

    # Parser Errors
    if opts.maximum is not None and opts.maximum <= 0:
        parser.error('option --max must be greater than zero')
    if opts.rvcontinue < 0:
        parser.error('option --start must be greater than or equal to zero')
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    wiki2snap(args[0], maximum=opts.maximum, rvcontinue=opts.rvcontinue,
        warm=opts.warm)


if __name__ == '__main__':
    parse_args()
    