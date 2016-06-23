#!/usr/bin/python
import libxml2
import os
import urllib2

WIKI = 'http://en.wikipedia.org/'

class WikiIter:
    """A WikiIter interprets a WikiMedia page history and returns revisions."""
    def __init__(self, wiki, title):
        # MediaWiki API query format.
        self.api = wiki+ 'w/index.php?title=Special:Export&pages=' + \
                    title.replace(' ', '+')+'&history&action=submit'
        self.rvid = 0 

        # If not in cache, download revision history and save to full_histories
        cachefile = os.path.join('full_histories', title.replace(" ", "_"))
        if not (os.path.isfile(cachefile)):
            doc= libxml2.parseDoc(urllib2.urlopen(self.api).read())
            cachefile = open(cachefile, 'w')
            doc.saveTo(cachefile, encoding='UTF-8', format=1)
            cachefile.close()



    #def next(self):
       # """next gets the next revision in this WikiIter."""

        # Get content.
        #rev = doc.xpathEval('/api/query/pages/page/revisions/rev')
        #assert len(rev) == 1

        # Get next iter.
        #qc = doc.xpathEval('/api/continue')
        #if len(qc) == 1:
        #    self.rvcontinue = qc[0].prop('rvcontinue')
        #elif len(qc) == 0:
        #    self.rvcontinue = None
        #else:
        #    assert False

        #return (rev[0].prop('revid'), rev[0].prop('comment'), rev[0].content)

it=WikiIter(WIKI, "Mesostigma")