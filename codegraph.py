#!/usr/bin/python

import argparse
import wiki2graph as w2g
import metric
import metric2color as m2c


def parse_args():
    parser = argparse.ArgumentParser(usage='%%prog [options] source')

    parser.add_argument('source', nargs=1)
    parser.add_argument('--repo-path', dest='repo_path', type=str, required=True,
                        help='Path to the repo the file lives in.')
    parser.add_argument('--name', dest='name', type=str, required=True,
                        help='The name of this analysis/output files')

    return parser.parse_args()


def code2color(name, source, repo_path):
    """Performs analysis on repo_path/source and outputs as 'name'"""

    # Create patch model if not cached
    file = '%s.txt' % name
    model = w2g.read_cached_model(file)
    if model is None:
        model = w2g.applyCodeModel(name, source, repo_path)

    # Create height model
    (graph, content, model) = model
    metricDict = metric.tHeight(graph)

    m2c.metric2color(name, False, name, metricDict)


if __name__ == '__main__':
    args = parse_args()
    code2color(args.name, args.source[0], args.repo_path)
