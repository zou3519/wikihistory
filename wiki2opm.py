#!/usr/bin/python
import optparse
import os
import sys

from opmgraph import OPMGraph
from patch import PatchSet, PatchModel
from progressbar import ProgressBar
from wikiiter import WikiIter


NAME = 'wiki2opm.py'
VERSION = 'v0.1'
WIKI = 'http://en.wikipedia.org/'


def wiki2opm(title, maximum=None, rvstartid=0, warm=False):
    """wiki2opm converts a WikiIter-able page history to an OPM graph file."""
    if not os.path.isdir('data'):
        os.mkdir('data')

    witer = WikiIter(WIKI, title, rvstartid=rvstartid)
    progress = ProgressBar('Processing "' + title + '"', maximum=maximum)
    if not warm:
        prev = []
        model = PatchModel()
        graph = OPMGraph.new_graph(NAME + '-' + VERSION)

    # For each revision...
    next = witer.next()
    i = 0
    while next is not None and (maximum is None or i < maximum):
        progress.next()

        if not warm:
            # psdiff against the previous revision.
            (revid, comment, content) = next
            content = content.split()
            ps = PatchSet.psdiff(revid, prev, content)

            # Apply to the PatchModel and write dependencies to graph.
            depends = model.apply_patchset(ps)
            graph.new_artifact(ps.psid, comment)
            for d_psid in depends:
                graph.new_wasDerivedFrom(d_psid, ps.psid)

            prev = content

        next = witer.next()
        i += 1

    sys.stdout.write(' done.\n')
    sys.stdout.flush()

    if not warm:
        print 'Saving graph...'
        graph.save_to(os.path.join('data', title.replace(' ', '_') + '-m' +
            str(i) + 's' + rvstartid + '.xml'))


def parse_args():
    """parse_args parses sys.argv for wiki2opm."""
    # Help Menu
    parser = optparse.OptionParser(usage='%prog [options] title')
    parser.add_option('-m', '--max',
                      type='int', dest='maximum', default=None,
                      help='process at most MAX revisions', metavar='MAX')
    parser.add_option('-s', '--start',
                      type='str', dest='rvstartid', default='0',
                      help='start from START revid', metavar='START')
    parser.add_option('-w', '--warm',
                      action='store_true', dest='warm', default=False,
                      help='warm the cache without processing')

    (opts, args) = parser.parse_args()

    # Parser Errors
    if opts.maximum is not None and opts.maximum <= 0:
        parser.error('option --max must be greater than zero')
    if opts.rvstartid < 0:
        parser.error('option --start must be greater than or equal to zero')
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    wiki2opm(args[0], maximum=opts.maximum, rvstartid=opts.rvstartid,
        warm=opts.warm)


if __name__ == '__main__':
    parse_args()
