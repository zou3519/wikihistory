import libxml2
import os
import urllib2


class WikiIter:
    """A WikiIter interprets a WikiMedia page history and returns revisions."""
    def __init__(self, wiki, title, rvstartid=0):
        # MediaWiki API query format.
        self.api = wiki + '/w/api.php?format=xml&action=query&titles=' + \
                   title.replace(' ', '+') + '&prop=revisions' + \
                   '&rvprop=ids|flags|timestamp|user|size|comment|content' + \
                   '&rvlimit=1&rvdir=newer&rvstartid='
        self.dir = os.path.join('cache', title)
        self.rvstartid = rvstartid # Revision ID iterator.

        if not os.path.isdir(self.dir):
            os.makedirs(self.dir)
        # XXX: Doesn't handle multiple wikis.

    def next(self):
        """next gets the next revision in this WikiIter."""
        if self.rvstartid is None:
            return None

        # Check cache; else, query MediaWiki.
        cachefile = os.path.join(self.dir, str(self.rvstartid))
        if os.path.isfile(cachefile):
            doc = libxml2.parseFile(cachefile)
        else:
            doc = libxml2.parseDoc(
                urllib2.urlopen(self.api + self.rvstartid).read())
            cachefile = open(cachefile, 'w')
            doc.saveTo(cachefile, encoding='UTF-8', format=1)
            cachefile.close()

        # Get content.
        rev = doc.xpathEval('/api/query/pages/page/revisions/rev')
        assert len(rev) == 1

        # Get next iter.
        qc = doc.xpathEval('/api/query-continue/revisions')
        if len(qc) == 1:
            self.rvstartid = qc[0].prop('rvstartid')
        elif len(qc) == 0:
            self.rvstartid = None
        else:
            assert False

        return (rev[0].prop('revid'), rev[0].prop('comment'), rev[0].content)
