#!/usr/bin/python

'''
Given a graph, returns an exploratory visualization of its
various vertices and edges. Used mainly for debugging the graph.

Run with 'examinegraph.py GMLs/something.txt'
'''

import argparse
import json
import errno
import shutil
from string import Template
from networkx.readwrite import json_graph
from wiki2graph import readGraph


graph_template_path = 'webtemplates/graph/'
graph_template_file = 'template.html'
graph_generation_path = 'webgraphs/'


def build_viz_from_file(name, gml_file):
    nx_graph = readGraph(gml_file)
    return build_viz_from_graph(name,nx_graph)


def build_viz_from_graph(name, nx_graph):
    elements = graph_to_cytoscope(nx_graph)

    # inject elements into new html file
    graph_path = graph_generation_path + name
    template_file = graph_path + '/' + graph_template_file
    copy(graph_template_path, graph_generation_path + name)
    new_content = ''

    with open(template_file, 'r') as content_file:
        template = Template(content_file.read())
        new_content = template.safe_substitute(elements=elements)
    with open(template_file, 'w') as content_file:
        content_file.write(new_content)


def graph_to_cytoscope(nx_graph):
    nodes = []
    edges = []
    data = json_graph.node_link_data(nx_graph)

    for node in data['nodes']:
        nodes.append({'data': node})

    for link in data['links']:
        edges.append({'data': link})

    return json.dumps({'nodes': nodes, 'edges': edges})


def copy(src, dest):
    try:
        shutil.copytree(src, dest)
    except OSError as e:
        # If the error was caused because the source wasn't a directory
        if e.errno == errno.ENOTDIR:
            shutil.copy(src, dest)
            return
        print('Directory not copied. Error: %s' % e)


def parse_args():
    parser = argparse.ArgumentParser(usage='%%prog gml_file')
    parser.add_argument('gml_file', nargs=1)
    parser.add_argument('--name', dest='name', type=str, required=True,
                        help='The name of the output directory')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    build_viz_from_file(args.name, args.gml_file[0])
