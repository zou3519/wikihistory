#!/usr/bin/python


# Contains all function that involve the full Wikipedia history
#    and forming the model/graph

import argparse
import os
import requests
import codecs
import textProcessor as proc
import networkx as nx
from Patch import PatchSet, PatchModel
import logging

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


def setup_cache():
    """Make folders for model, graph, and content files"""
    if not os.path.isdir('GMLs'):
        os.mkdir('GMLs')
    if not os.path.isdir('models'):
        os.mkdir('models')
    if not os.path.isdir('content'):
        os.mkdir('content')


def save_to_cache(cachefile, model, content):
    """Save graph, model, and content to cache"""

    # Writes graph to file
    nx.write_gml(model.graph, "GMLs/" + cachefile)

    # Write model to file
    modelFile = open("models/" + cachefile, "w")
    line = ""
    for patch in model.model:
        line += str(patch[0]) + ' ' + str(patch[1]) + '\n'
    modelFile.write(line)
    modelFile.close()

    # Write content to file
    contentFile = open("content/" + cachefile, "w")
    contentFile.write(content)
    contentFile.close()


def applyModel2():
    logging.basicConfig(filename='example.log',level=logging.INFO)
    file = "src/acquire/engine/Engine.scala"
    title = "engine"

    # Make folders for model, graph, and content files
    setup_cache()

    print "Setting up distance comparison . . ."

    distance_model = proc.BasicDistanceModel(title)

    model = PatchModel()
    prev = ""
    pid = 0
    offset = 0

    git_repo = proc.GitRepo("/home/rzou/acquire")
    for (rvid, timestamp, content) in proc.GitRepoIter(git_repo, file, offset):

        # Get semantic distance
        dist = distance_model.score(prev, content)

        # Apply PatchModel
        content = content.encode("ascii", "replace")
        contentList = content.split()
        prevList = prev.split()
        ps = PatchSet.psdiff(pid, prevList, contentList)
        pid += len(ps.patches)
        for p in ps.patches:
            # list of out-edges from rev
            model.apply_patch(p, timestamp, dist)

        prev = content

    cachefile = title + '.txt'
    save_to_cache(cachefile, model, content)
    return model.graph, content, model.model


def applyModel(title, remove):
    """
        Applies PatchModel to the history for Wikipedia page, title.
        Returns the full history tranformed into a graph according to the model,
            the PatchModel, and the most recent content.
    """

    title = title.replace(" ", "_")

    # Make folders for model, graph, and content files
    setup_cache()

    print "Setting up distance comparison . . ."
    semantic_model = proc.SemanticDistanceModel(title)

    # Get the list of vertices to remove
    if remove:
        remList = getRemlist(title)

    print "Applying model . . ."

    model = PatchModel()
    prev = ""
    pid = 0
    offset = '0'

    for (rvid, timestamp, content) in proc.WikiIter(title, offset):

        # Apply to the PatchModel and write dependencies to graph.
        if remove and rvid in remList:
            remList.remove(rvid)
            continue

        # Get semantic distance
        dist = semantic_model.score(prev, content)

        # Apply PatchModel
        content = content.encode("ascii", "replace")
        contentList = content.split()
        prevList = prev.split()
        ps = PatchSet.psdiff(pid, prevList, contentList)
        pid += len(ps.patches)
        for p in ps.patches:
            # list of out-edges from rev
            model.apply_patch(p, timestamp, dist)

        prev = content

    cachefile = title + ('_rem.txt' if remove else '.txt')
    save_to_cache(cachefile, model, content)
    return model.graph, content, model.model


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


def readGraph(title, remove):
    """
        Reads a networkx graph from a file for Wikipedia page, title, with
            remove 
    """
    print "Reading graph . . ."
    if remove:
        file = "GMLs/" + title.replace(" ", "_") + '_rem.txt'
    else:
        file = "GMLs/" + title.replace(" ", "_") + '.txt'

    assert os.path.isfile(file), "Graph file does not exist."

    return nx.read_gml(file)


def readContent(title, remove):
    """
        Reads and returns a string from a file
    """
    print "Reading content . . ."

    if remove:
        file = "content/" + title.replace(" ", "_") + "_rem.txt"
    else:
        file = "content/" + title.replace(" ", "_") + ".txt"

    assert os.path.isfile(file), "Content file does not exist."

    contentFile = open(file, "r")
    content = ""
    for line in contentFile:
        content += line
    contentFile.close()
    return content


def readModel(title, remove):
    """
        Reads and returns a PatchModel from a file
    """
    print "Reading model . . ."
    if remove:
        file = "models/" + title.replace(" ", "_") + "_rem.txt"
    else:
        file = "models/" + title.replace(" ", "_") + ".txt"

    assert os.path.isfile(file), "Model file does not exist."

    modelFile = open(file, "r")
    model = []

    # Read model
    for line in modelFile:
        line = line.split()
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
        file = title.replace(" ", "_") + "_rem.txt"
    else:
        file = title.replace(" ", "_") + ".txt"

    # Check if files exist to avoid reapplying model
    if not new and \
            os.path.isdir('GMLs') and os.path.isfile("GMLs/" + file) and \
            os.path.isdir('content') and os.path.isfile("content/" + file) and \
            os.path.isdir('models/') and os.path.isfile("models/" + file):

        graph = readGraph(title, remove)
        content = readContent(title, remove)
        model = readModel(title, remove)

    # Apply model. Download full history if necessary
    else:
        if not os.path.isdir('full_histories') or not os.path.isdir("full_histories/" + title.replace(' ', '_')):
            downloadHistory(title)
        # (graph, content, model) = applyModel2()
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

    n = parser.parse_args()

    wiki2graph(n.title[0], n.remove, n.new)


if __name__ == '__main__':
    parse_args()
