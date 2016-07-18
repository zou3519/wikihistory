#!/usr/bin/python
import bisect
import cmd
import math
import optparse
import os
import os.path
import random
import sys

import metrics
import oracles
from opmgraph import OPMGraph


NAME = 'truncate.py'
VERSION = 'v0.1'


def load_csv(filename, metric=metrics.MetricType.PROVRANK):
    """
    load_csv loads a column seperated vector file in the following format:
    nid,provrank,subrank,label
    """
    csv = open(filename, 'r')
    adj = {}
    labels = {}
    scoremap = {}

    # Load nodes.
    for line in csv:
        if line == '\n': break
        (nid, pr, sr, label) = line.strip().split(',', 3)

        adj[nid] = set()
        labels[nid] = os.path.basename(label)
        if metric == metrics.MetricType.PROVRANK:
            scoremap[nid] = float(pr)
        elif metric == metrics.MetricType.SUBRANK:
            scoremap[nid] = float(sr)
        else:
            assert False

    # Load edges.
    for line in csv:
        (cid, pid) = line.strip().split(',')
        adj[cid].add(pid)

    return (adj, labels, scoremap)


def to_dot(filename, adj, nids, color=False, labels=None, scoremap=None):
    """
    to_dot writes nids in adj to filename in dot format.
    opts:
        color: write all nodes in adj, but color nodes in nids
        labels: mark nodes with labels instead of ids
        scoremap: color nodes with log spectrum based on score
    """
    dotfile = open(filename, 'w')
    if scoremap is not None:
        min_score = min(scoremap.values())
        scale = pow(max(scoremap.values()) / min_score, 1.0/10)

    dotfile.write('digraph OPMGraph { rankdir="BT";\n')

    # Write nodes.
    for nid in sorted(nids) if not color else sorted(adj):
        dotfile.write(str(nid) + ' [label="' + (str(labels[nid]) if labels is not None else str(nid)) + '"')

        if color and nid in nids:
            dotfile.write(',style=filled,fillcolor=red]\n')
        elif scoremap is not None:
            spectrum = int(round(math.log(scoremap[nid] / min_score, scale))) + 1
            dotfile.write(',style=filled,fillcolor="/spectral11/' + str(spectrum) + '"]\n')
        else:
            dotfile.write(']\n')

    # Write edges.
    for nid in sorted(nids) if not color else sorted(adj):
        for pid in sorted(adj[nid]):
            if not color and pid not in nids: continue
            dotfile.write(str(nid) + ' -> ' + str(pid) + ' [style="bold"]\n')

    dotfile.write('}')
    dotfile.close()


def query(filename, csv=False, input=None, metric=metrics.MetricType.PROVRANK):
    """
    query starts a command prompt that allows the user to query and truncate
    an OPM XML file, given a metric [default ProvRank].
    """
    # Load the graph.
    outfile = os.path.splitext(filename)[0]
    if not csv:
        sys.stdout.write('Loading graph...')
        sys.stdout.flush()

        (adj, labels) = OPMGraph.parse_file(filename).get_adj_labels()

        sys.stdout.write('done.\n')
        sys.stdout.flush()

        # Compute metrics.
        if metric == metrics.MetricType.PROVRANK:
            scoremap = metrics.provrank(adj)
            outfile += '-p-'
        elif metric == metrics.MetricType.SUBRANK:
            scoremap = metrics.subrank3(adj)
            outfile += '-s-'
        else:
            assert False
    else:
        graph = None
        (adj, labels, scoremap) = load_csv(filename, metric=metric)
        if metric == metrics.MetricType.PROVRANK:
            outfile += '-p-'
        elif metric == metrics.MetricType.SUBRANK:
            outfile += '-s-'
        else:
            assert False

    # Enter a command prompt.
    class query_prompt(cmd.Cmd):
        # COMMAND analyze
        def help_analyze(self): print 'usage: analyze nid'
        def do_analyze(self, line):
            nid = line.strip()
            result = metrics.analyze(adj, scoremap, nid)
            print 'Best threshold: ' + str(result)

        def help_a(self): return self.help_analyze()
        def do_a(self, line): return self.do_analyze(line)

        # COMMAND evaluate
        def help_evaluate(self): print 'usage: evaluate [opts]'
        def do_evaluate(self, line):
            # Parse opts.
            i = 0
            opts = line.split()
            authors = None
            bridges = False
            cuts = None
            empty = False
            leaves = False
            maximum = None
            reversions = False
            sources = False

            while i < len(opts):
                if opts[i] == '--authors' or opts[i] == '-a':
                    authors = oracles.authors(adj, labels, prettyprint=True)
                elif opts[i] == '--bridges' or opts[i] == '-b':
                    bridges = True
                elif opts[i] == '--cuts' or opts[i] == '-c':
                    try:
                        i += 2
                        cuts = (opts[i - 1], int(opts[i]))
                    except IndexError, ValueError:
                        return self.help_evaluate()
                elif opts[i] == '--empty' or opts[i] == '-e':
                    empty = True
                elif opts[i] == '--max' or opts[i] == '-m':
                    try:
                        i += 1
                        maximum = int(opts[i])
                    except IndexError, ValueError:
                        return self.help_evaluate()
                elif opts[i] == '--leaves' or opts[i] == '-l':
                    leaves = True
                elif opts[i] == '--reversions' or opts[i] == '-r':
                    reversions = True
                elif opts[i] == '--sources' or opts[i] == '-s':
                    sources = True
                i += 1
            if sum((authors is not None, bridges, cuts is not None, empty, reversions, sources)) != 1: return self.help_evaluate()

            # Get the oracle.
            if authors is not None:
                oracle = oracles.authors(adj, labels)
            elif bridges:
                oracle = oracles.bridges(adj)
            elif cuts is not None:
                (source, k) = cuts
                sink = str(min([int(nid) for nid in adj]))
                oracle = oracles.cuts(adj, source, sink, k)
            elif empty:
                oracle = lambda query, cid, nid: False
            elif reversions:
                oracle = oracles.reversions(adj, labels)
            elif sources:
                oracle = oracles.sources(adj, labels)

            # Evaluate.
            result = metrics.evaluate(adj, scoremap, oracle, labels, leaves=leaves, maximum=maximum, testset=authors)

            # Save.
            postfix = 'e'
            if authors is not None: postfix += 'a'
            elif bridges: postfix += 'b'
            elif cuts is not None: postfix += source + 'c' + str(k)
            elif empty: postfix += 'e'
            elif reversions: postfix += 'r'
            elif sources: postfix += 's'
            if leaves: postfix += 'l'
            if maximum is not None: postfix += 'm' + str(maximum)

            evalfile = open(outfile + postfix + '.dat', 'w')
            for (nid, (t_size, o_size, i_size)) in result:
                evalfile.write(nid + ' ' + str(t_size) + ' ' + str(o_size) + ' ' + str(i_size) + ' ' + str(abs(t_size - o_size)) + ' ' + str(max(i_size - o_size, o_size)) + '\n')
            evalfile.close()

        def help_e(self): return self.help_evaluate()
        def do_e(self, line): return self.do_evaluate(line)

        def help_oracle(self): print 'usage: oracle [opts]'
        def do_oracle(self, line):
            # Parse opts.
            i = 0
            opts = line.split()
            authors = False
            bridges = False
            color = True
            cuts = None
            reversions = False
            sources = False

            while i < len(opts):
                if opts[i] == '--authors' or opts[i] == '-a':
                    authors = True
                    color = False
                elif opts[i] == '--bridges' or opts[i] == '-b':
                    bridges = True
                elif opts[i] == '--cuts' or opts[i] == '-c':
                    try:
                        i += 2
                        cut = (opts[i - 1], int(opts[i]))
                    except IndexError, ValueError:
                        return self.help_evaluate()
                elif opts[i] == '--reversions' or opts[i] == '-r':
                    reversions = True
                elif opts[i] == '--sources' or opts[i] == '-s':
                    sources = True
                i += 1
            if sum((authors, bridges, cuts is not None, reversions, sources)) != 1: return self.help_oracle()

            # Get the oracle.
            if authors:
                oracle = oracles.authors(adj, labels, prettyprint=True)
            elif bridges:
                oracle = oracles.bridges(adj, prettyprint=True)
            elif cuts is not None:
                (source, k) = cut
                sink = str(min([int(nid) for nid in adj]))
                oracle = oracles.cuts(adj, source, sink, k, prettyprint=True)
            elif reversions:
                oracle = oracles.reversions(adj, labels, prettyprint=True)
            elif sources:
                oracle = oracles.sources(adj, labels, prettyprint=True)

            # Save.
            postfix = 'o'
            if authors: postfix += 'a'
            elif bridges: postfix += 'b'
            elif cuts is not None: postfix += source + 'c' + str(k)
            elif reversions: postfix += 'r'
            elif sources: postfix += 's'
            to_dot(outfile + postfix + '.dot', adj, oracle, color=color)

        def help_o(self): return self.help_oracle()
        def do_o(self, line): return self.do_oracle(line)

        # COMMAND plot
        def help_plot(self): print 'usage: plot nid'
        def do_plot(self, line):
            nid = line.strip()
            result = metrics.plot(adj, scoremap, nid)
            postfix = nid + 'p'
            plotfile = open(outfile + postfix + '.dat', 'w')
            for (threshold, set_size) in result:
                plotfile.write(str(threshold) + ' ' + str(set_size) + '\n')
            plotfile.close()

        def help_p(self): return self.help_plot()
        def do_p(self, line): return self.do_plot(line)

        # COMMAND sample
        def help_sample(self): print 'usage: sample nid'
        def do_sample(self, line):
            nid = line.strip()
            result = metrics.sample(adj, scoremap, nid)
            postfix = nid + 'sa'
            samplefile = open(outfile + postfix + '.dat', 'w')
            for (threshold, set_size) in result:
                samplefile.write(str(threshold) + ' ' + str(set_size) + '\n')
            samplefile.close()

        def help_sa(self): return self.help_sample()
        def do_sa(self, line): return self.do_sample(line)

        # COMMAND spectrum
        def help_spectrum(self): print 'usage: spectrum [opts]'
        def do_spectrum(self, line):
            # Parse line.
            label = None
            for opt in line.split():
                if opt == '--label' or opt == '-l': label = True
                else: return self.help_spectrum()

            # Save.
            postfix = 'sp'
            if label: postfix += 'l'; label = labels
            to_dot(outfile + postfix + '.dot', adj, adj.keys(), labels=label, scoremap=scoremap)

        def help_sp(self): return self.help_spectrum()
        def do_sp(self, line): return self.do_spectrum(line)

        # COMMAND truncate
        def help_truncate(self): print 'usage: truncate [opts] nid threshold'
        def do_truncate(self, line):
            # Parse line.
            try:
                (opts, nid, threshold) = line.rsplit(' ', 2)
                opts = opts.split()
                threshold = float(threshold)
            except ValueError:
                try:
                    (nid, threshold) = line.rsplit(' ', 1)
                    opts = []
                    threshold = float(threshold)
                except ValueError:
                    return self.help_truncate()

            # Parse opts.
            color = False
            label = None
            spectrum = None
            for opt in opts:
                if opt == '--color' or opt == '-c': color = True
                elif opt == '--label' or opt == '-l': label = True
                elif opt == '--spectrum' or opt == '-s': spectrum = True
                else: return self.help_truncate()

            # Truncate.
            result = metrics.truncate(adj, scoremap, nid, threshold)

            # Save.
            postfix = nid + 't' + str(threshold)
            if color: postfix += 'c'
            if label: postfix += 'l'; label = labels
            if spectrum: postfix += 's'; spectrum = scoremap
            to_dot(outfile + postfix + '.dot', adj, result, color=color, labels=label, scoremap=spectrum)

        def help_t(self): return self.help_truncate()
        def do_t(self, line): return self.do_truncate(line)

        # COMMAND quit
        def help_quit(self): print 'usage: quit'
        def do_quit(self, line):
            return 1

        def help_q(self): return self.help_quit()
        def do_q(self, line): return self.do_quit(line)

    prompt = query_prompt()

    ret = 0
    if input is not None:
        for line in input.split(';'):
            ret = prompt.onecmd(line.strip())
            if ret == 1: break

    if ret != 1:
        prompt.cmdloop()


def parse_args():
    """parse_args parses sys.argv for query."""
    # Help Menu
    parser = optparse.OptionParser(usage='%prog [options] file')
    parser.add_option('-c', '--csv',
                      action='store_true', dest='csv', default=False,
                      help='load input file as csv')
    parser.add_option('-i', '--input',
                      action='store', type='string', dest='input', default=None,
                      help='input a sequence of semicolon-separated commands')
    parser.add_option('-p', '--provrank',
                      action='store_true', dest='provrank', default=False,
                      help='use provrank [default]')
    parser.add_option('-s', '--subrank',
                      action='store_true', dest='subrank', default=False,
                      help='use subrank')

    (opts, args) = parser.parse_args()

    # Parser Errors
    if opts.provrank and opts.subrank:
        parser.error('options --provrank and --subrank are exclusive')
    if len(args) != 1:
        parser.error('incorrect number of arguments')

    if opts.provrank:
        query(args[0], csv=opts.csv, input=opts.input, metric=metrics.MetricType.PROVRANK)
    elif opts.subrank:
        query(args[0], csv=opts.csv, input=opts.input, metric=metrics.MetricType.SUBRANK)
    else:
        query(args[0], csv=opts.csv, input=opts.input)


if __name__ == '__main__':
    parse_args()
