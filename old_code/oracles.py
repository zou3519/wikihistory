import bisect
import os.path
import re

from pygraph.algorithms.minmax import maximum_flow
from pygraph.classes.digraph import digraph
from pygraph.classes.exceptions import AdditionError


def authors(adj, labels, prettyprint=False):
    """
    authors returns an oracle that terminates at the borders of the workflow
    defined by the 1st Provenance Challenge's authors.
    """
    # Find the basic challenge components.(?<!...)
    nidfilter = re.compile(r'(\d+(?<!5124|5128)\.0|' +
                           r'(347|348|350|352|353|354|355|356)\.1)$')
    challenge = re.compile(r'(anatomy[1234]\.(hdr|img)|' +
                            r'align_warp|' +
                            r'warp[1234]\.warp|' +
                            r'reslice|' +
                            r'resliced[1234]\.(hdr|img)|' +
                            r'softmean|' +
                            r'atlas\.(hdr|img)|' +
                            r'slicer|' +
                            r'fakeslicer|'
                            r'atlas-[xyz]\.pgm|' +
                            r'pgmtoppm|' +
                            r'pnmtojpeg|' +
                            r'atlas-[xyz]\.jpg)$')

    base = set()
    for nid in adj:
        if nidfilter.match(nid) is None and challenge.match(os.path.basename(labels[nid])) is not None:
            base.add(nid)

    # Find pipes.
    nids = set(base)
    for cid in base:
        for pid in adj[cid]:
            if labels[pid] == '' and adj[pid].intersection(base) is not None:
                nids.add(pid)

    if not prettyprint:
        return lambda query, cid, nid: nid not in nids
    else:
        return nids


def bridges(adj, prettyprint=False):
    """
    bridges returns an oracle that terminates at bridges in adj
    """
    # Needs an undirected graph.
    und = dict([(nid, set(adj[nid])) for nid in adj])
    for cid in adj:
        for pid in adj[cid]:
            und[pid].add(cid)

    # Algorithm: An edge is a bridge iff it is not contained in a cycle. So,
    # DFS, and whenever you encounter a cycle, contract it. Repeat until the
    # DFS finds no cycle, then step backwards, deleting nodes and adding
    # bridges as you go.
    path = [] # The DFS path.
    part = [] # The partitioning of the DFS path into contracted supernodes.
    asgn = dict([(nid, -1) for nid in und]) # Supernode assignment of nodes.
    cnt = [len(und) - 1] # Generator for supernode IDs.
    ret = set()

    def bdfs(u, v):
        path.append(v)
        part.append(len(path) - 1)
        asgn[v] = len(path) - 1

        for w in und[v]:
            if asgn[w] == -1:
                bdfs(v, w)
            # If DFS finds a loop, contract.
            elif w != u:
                while part[-1] > asgn[w]:
                    part.pop()

        if part[-1] == asgn[v]:
            part.pop()
            cnt[0] += 1
            while len(path) - 1 >= asgn[v]:
                asgn[path.pop()] = cnt[0]
            if u != -1:
                if int(u) > int(v):
                    ret.add((u, v))
                else:
                    ret.add((v, u))

    for nid in asgn:
        if asgn[nid] == -1:
            bdfs(-1, nid)

    if not prettyprint:
        return lambda query, cid, nid: (cid, nid) in ret
    else:
        return set([nid for (cid, nid) in ret])


def cuts(adj, source, sink, k, prettyprint=False):
    """
    cuts returns an oracle that terminates at all cuts between source and sink
    with capacity less than or equal to k.
    """
    # Convert adj to a cut-able pygraph.
    graph = digraph()
    for nid in adj:
        graph.add_node(nid)
    for cid in adj:
        for pid in adj[cid]:
            graph.add_edge((cid, pid))

    ret = set()
    while True:
        (flow, asgn) = maximum_flow(graph, source, sink)

        # Find the minimum cut.
        mincut = set()
        for (u, v) in flow:
            if flow[(u, v)] > 0 and asgn[u] != asgn[v]:
                mincut.add((u, v))

        # If it's too large, we're done; break.
        maxflow = 0
        for edge in mincut:
            maxflow += flow[edge]
        if 0 < maxflow and maxflow <= k:
            ret.update(mincut)
        else:
            break

        # Reweight one edge in the cut so that it will no longer be min.
        edge = max([(int(u), int(v)) for (u,v) in mincut])
        edge = (str(edge[0]), str(edge[1]))
        graph.del_edge(edge)
        graph.add_edge(edge, wt=len(adj))

    if not prettyprint:
        return lambda query, cid, nid: (cid, nid) in ret
    else:
        return set([nid for (cid, nid) in ret])


def sources(adj, labels, prettyprint=False):
    """
    sources returns an oracle that terminates at source files: .c, .h, or .S
    """
    pattern = re.compile(r'.+\.([ch]|so(\..+)?)$')
    nids = set()
    for nid in adj:
        if pattern.match(os.path.basename(labels[nid])) is not None:
            nids.add(nid)

    if not prettyprint:
        return lambda query, cid, nid: nid in nids
    else:
        return nids


def reversions(adj, labels, prettyprint=False):
    """
    reversions returns an oracle that terminates at all revisions prior to the
    most recent comment containing the phrase "revert".
    """
    wp = re.compile(r'[Rr]evert')

    nids = set((0,))
    for nid in adj:
        if wp.search(labels[nid]) is not None:
            nids.add(nid)

    if not prettyprint:
        nids = sorted([int(nid) for nid in nids])
        return lambda query, cid, nid: nids[bisect.bisect(nids, int(query)) - 1] > int(nid)
    else:
        return nids
