#!/usr/bin/python


# Contains all function that involve the full Wikipedia history
#    and forming the model/graph

import argparse
import os
import codecs
import logging
import networkx as nx
from Patch import PatchSet, PatchModel
from wikiprocessor import WikiIter
from semanticdistancemodel import SemanticDistanceModel
from distancemodels import BasicDistanceModel
from gitprocessor import GitRepo, GitRepoIter


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

    # Make cache folders if they don't exist
    setup_cache()

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
    logging.basicConfig(filename='example.log', level=logging.INFO)
    file = "src/acquire/engine/Engine.scala"
    title = "engine"

    print "Setting up distance comparison . . ."

    distance_model = BasicDistanceModel(title)

    model = PatchModel()
    prev = ""
    pid = 0
    offset = 0

    git_repo = GitRepo("/home/rzou/acquire")
    for (rvid, timestamp, content) in GitRepoIter(git_repo, file, offset):

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


def applyWikiModel(title, remove):
    title = safe_title(title)
    semantic_model = SemanticDistanceModel(title)
    wiki_history_iterable = WikiIter(title, '0', remove)
    return buildPatchModel(wiki_history_iterable, semantic_model)


def buildPatchModel(doc_iterable, dist_model):
    patch_model = PatchModel()
    prev_content = ''
    patchid = 0

    for (rvid, timestamp, content) in doc_iterable:
        content = content.encode('ascii', 'replace')

        # Compute distance between revisions
        dist = dist_model.score(prev_content, content)

        # Compute patches
        content_list = content.split()
        prev_content_list = prev_content.split()
        patch_set = PatchSet.psdiff(patchid, prev_content_list, content_list)
        patchid += len(patch_set.patches)

        # Present patches to patch model
        for patch in patch_set.patches:
            patch_model.apply_patch(patch, timestamp, dist)

        prev_content = content

    cachefile = safe_title(doc_iterable.title) + \
        ('_rem.txt' if doc_iterable.use_blacklist else '.txt')
    save_to_cache(cachefile, patch_model, content)
    return patch_model.graph, content, patch_model.model


def safe_title(title):
    return title.replace(" ", "_")


def readGraph(file):
    """Reads a networkx graph from a file for Wikipedia page"""
    print "Reading graph . . ."
    assert os.path.isfile(file), "Graph file does not exist."
    return nx.read_gml(file)


def readContent(file):
    """Reads and returns a string from a file"""
    print "Reading content . . ."
    assert os.path.isfile(file), "Content file does not exist."

    contentFile = open(file, "r")
    content = ""
    for line in contentFile:
        content += line
    contentFile.close()
    return content


def readModel(file):
    """Reads and returns a PatchModel from a file"""
    print "Reading model . . ."

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
    file = title.replace(" ", "_") + ("_rem" if remove else "") + ".txt"

    # Check if files exist to avoid reapplying model
    if not new and \
            os.path.isdir('GMLs') and os.path.isfile("GMLs/" + file) and \
            os.path.isdir('content') and os.path.isfile("content/" + file) and \
            os.path.isdir('models/') and os.path.isfile("models/" + file):

        graph = readGraph('GMLs/' + file)
        content = readContent('content/' + file)
        model = readModel('models/' + file)
        return (graph, content, model)

    # Apply model.
    # (graph, content, model) = applyModel2()
    (graph, content, model) = applyWikiModel(title, remove)

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
