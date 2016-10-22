import gensim
import os
import codecs
import requests
import timestamp as ts


class WikiIter(object):
    """Iterates through revisions of a Wiki article"""

    def __init__(self, title, offset, remove):
        self.title = title
        self.offset = offset

        # If we haven't gotten the full history of the file, get it.
        if not self.is_history_cached():
            downloadHistory(title)

        # Get a list of revisions NOT to include
        self.use_blacklist = remove
        self.rev_blacklist = {}
        if remove:
            self.rev_blacklist = frozenset(getRemlist(title.replace(' ', '_')))

    def is_history_cached(self):
        if not os.path.isdir('full_histories'):
            return False

        cached_location = 'full_histories/%s' % self.title.replace(' ', '_')
        return os.path.isdir(cached_location)

    def __iter__(self):
        title = self.title
        offset = self.offset

        title = title.replace(" ", "_")

        getid = True  # can read id from doc
        gettime = False  # have id ready to use, can read time from doc
        gettext = False   # have an id ready to use
        process = False  # ready to use content
        writeText = False  # adding to current content

        # TODO(rzou): is the full history thing even right? offset is weird.
        while os.path.isfile('full_histories/' + title + '/' + title + '|' + offset + '.xml'):
            historyFile = codecs.open(
                'full_histories/' + title + '/' + title + '|' + offset + '.xml', "r", "utf-8")

            line = historyFile.readline().strip()
            while line[:4] != "<id>":
                line = historyFile.readline().strip()

            for line in historyFile:
                line = line.strip()

                # Gets the next revision id
                if getid:
                    if line[:4] == "<id>":
                        rvid = line[4:-5]
                        getid = False
                        gettime = True

                # Gets the timestamp of the revision
                if gettime:
                    if line[:11] == "<timestamp>":
                        timestamp = line[11:-12]
                        offset = timestamp
                        gettime = False
                        gettext = True

                # Have an id ready to use, looking for start of content
                if gettext:
                    if line[:5] == "<text":
                        content = ""
                        line = line.split('">')
                        if len(line) == 1:
                            line += [""]
                        line = line[1] + "\n"
                        gettext = False
                        writeText = True

                # Have reached start if content, looking for end
                if writeText:
                    if line[-7:] == "</text>":
                        content += line[:-7]
                        writeText = False
                        process = True
                    else:
                        content += line + "\n"

                if process:
                    getid = True
                    process = False
                    content = gensim.corpora.wikicorpus.filter_wiki(content)
                    datetime = ts.wiki_timestamp_to_datetime(timestamp)
                    unix_timestamp = ts.datetime_to_unix_timestamp(datetime)

                    # Enforce the revisions blacklist
                    if rvid in self.rev_blacklist:
                        continue

                    yield rvid, unix_timestamp, content

        # TODO(rzou) I don't think this is in the right place
        historyFile.close()


WIKI = 'https://en.wikipedia.org/'
LIMIT = '1000'


def downloadHistory(title):
    """
        Downloads the full history of Wikipedia page, title, into
            full_histories
    """
    print "Downloading . . ."
    offset = '0'
    i = 0
    while offset != '1':
        print "Starting set " + str(i) + " . . ."
        i += 1
        offset = downloadPartial(title, offset)


def downloadPartial(title, offset):
    """
        Downloads up to 1000 revisions of a Wikipedia page, title
            starting at offset.
        Offset '0' gets the first revision.
    """
    title = title.replace(' ', '_')
    api = WIKI + 'w/index.php?title=Special:Export&pages=' + title + \
        '&offset=' + offset + '&limit=' + LIMIT + '&action=submit'

    # Set up folder for the new history, if needed
    if not os.path.isdir('full_histories'):
        os.mkdir('full_histories')
    if not os.path.isdir('full_histories/' + title):
        os.mkdir('full_histories/' + title)

    cachefile = 'full_histories/' + title + '/' + title + '|' + offset + '.xml'
    file = open(cachefile, "w")

    # Download and save history
    r = requests.post(api, data="")
    last = True
    text = r.text.split('\n')
    file = codecs.open(cachefile, "w", "utf-8")
    for line in text:
        if last:
            if line.strip() == '<page>':
                last = False
        else:
            if line.strip()[:11] == '<timestamp>':
                date = line.strip(' ')
                date = date[11:-12]
        file.write(line + '\n')
    file.close()

    # Return offset of next revision
    if last:
        os.remove(cachefile)
        return '1'
    else:
        return date


def getRemlist(title):
        """
            Gets a list of ids of revisions that are bot reverts
            or that were reverted by bots
        """
        print "Removing bot rv."
        offset = '0'
        remList = []
        title = title.replace(" ", "_")

        while os.path.isfile('full_histories/' + title + '/' + title + '|' + offset + '.xml'):

            file = codecs.open('full_histories/' + title + '/' +
                               title + '|' + offset + '.xml', "r", "utf-8")

            username = False

            for line in file:
                line = line.strip()

                if not username and line[:4] == "<id>":
                    rvid = line[4:-5]

                if line[:10] == "<username>":
                    username = True
                else:
                    username = False

                if line[:10] == "<parentid>":
                    parentid = line[10:-11]

                elif line[:11] == '<timestamp>':
                    offset = line[11:-12]

                elif line[:9] == "<comment>":
                    if "BOT - rv" in line:
                        remList.append(rvid)
                        remList.append(parentid)

            file.close()
        return remList
