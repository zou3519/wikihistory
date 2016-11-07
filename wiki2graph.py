#!/usr/bin/python


# Contains all function that involve the full Wikipedia history
#    and forming the model/graph

import argparse
import os
import networkx as nx
from Patch import PatchSet, PatchModel
from wikiprocessor import WikiIter
from semanticdistancemodel import SemanticDistanceModel
from distancemodels import BasicDistanceModel
from gitprocessor import GitRepo, GitRepoIter


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


def wiki2graph(title, remove, new):
    """
        Returns a networkx graph, the content of the latest revision, and the
            PatchModel for Wikipedia page, title.
        Setting remove to True removes bot reverses and vandalism from the data.
        Setting new to True applies the model whether or not it is cached
    """
    file = title.replace(" ", "_") + ("_rem" if remove else "") + ".txt"

    # Check if files exist to avoid reapplying model
    cached_model = read_cached_model(file)
    if cached_model is not None:
        print "returning cached model"
        return cached_model

    # Apply model.
    print "applying model"
    return applyWikiModel(title, remove)


def read_cached_model(file):
    graphfile = 'GMLs/' + file
    contentfile = 'content/' + file
    modelfile = 'models/' + file

    if os.path.isdir('GMLs') and os.path.isfile(graphfile) and \
            os.path.isdir('content') and os.path.isfile(contentfile) and \
            os.path.isdir('models') and os.path.isfile(modelfile):
        graph = readGraph(graphfile)
        content = readContent(contentfile)
        model = readModel(modelfile)
        return (graph, content, model)

    return None


def applyWikiModel(title, remove):
    title = safe_title(title)
    semantic_model = SemanticDistanceModel(title)
    wiki_history_iterable = WikiIter(title, '0', remove)
    return buildPatchModel(wiki_history_iterable, semantic_model)


def applyCodeModel(name, source, repo_path):
    git_repo = GitRepo(repo_path)
    offset = 0  # Do not change, other offsets probably don't work.

    code_iterable = GitRepoIter(name, git_repo, source, offset)
    distance_model = BasicDistanceModel(name)

    return buildPatchModel(code_iterable, distance_model)


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
        patch_set = PatchSet.psdiff(patchid, prev_content_list, content_list, rvid)
        patchid += len(patch_set.patches)

        # Present patches to patch model
        for patch in patch_set.patches:
            patch_model.apply_patch(patch, timestamp, dist)

        prev_content = content

    # todo: get rid of document_name and using_blacklist
    cachefile = safe_title(doc_iterable.document_name) + \
        ('_rem.txt' if doc_iterable.using_blacklist else '.txt')
    save_to_cache(cachefile, patch_model, content)
    return patch_model.graph, content, patch_model.model


def safe_title(title):
    return title.replace(" ", "_")


def save_to_cache(cachefile, model, content):
    """Save graph, model, and content to cache"""

    # Make cache folders if they don't exist
    if not os.path.isdir('GMLs'):
        os.mkdir('GMLs')
    if not os.path.isdir('models'):
        os.mkdir('models')
    if not os.path.isdir('content'):
        os.mkdir('content')

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


if __name__ == '__main__':
    parse_args()
