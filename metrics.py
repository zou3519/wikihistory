import bisect
import os.path
import random
import sys
import time

from bitstring import BitString

from progressbar import ProgressBar


PROVRANK_ITER = 10000 # The number of ProvRank iterations (greater => accurate).


class MetricType:
    """MetricType enumerates the types of metrics: ProvRank and SubRank."""
    PROVRANK = 0
    SUBRANK = 1


def provrank(adj):
    """
    provrank takes an adjacency dictionary in (nid, pids) format and returns a
    dictionary mapping nids to their ProvRank.
    """
    PREV = 0
    NEXT = 1

    progress = ProgressBar('Computing ProvRank', maximum=PROVRANK_ITER)
    scoremap = dict([(nid, [1.0 / len(adj), 1.0 / len(adj)]) for nid in adj])

    # Compute ProvRank.
    for i in range(0, PROVRANK_ITER):
        progress.next()

        # Compute next iteration of ProvRank per-node.
        teleport = 0.0
        total_score = 1.0

        for cid in adj:
            # Push scores to parents, or teleport.
            if adj[cid]:
                for pid in adj[cid]:
                    scoremap[pid][NEXT] += scoremap[cid][PREV]
                    total_score += scoremap[cid][PREV]
            else:
                teleport += scoremap[cid][PREV] / len(adj)
                total_score += scoremap[cid][PREV]

        # Add teleportation and normalize.
        for nid in adj:
            scoremap[nid][NEXT] += teleport
            scoremap[nid][NEXT] = scoremap[nid][NEXT] / total_score
            scoremap[nid][PREV] = scoremap[nid][NEXT]

    sys.stdout.write(' done.\n')
    sys.stdout.flush()

    return dict([(nid, next) for (nid, (prev, next)) in scoremap.items()])


def subrank(adj):
    """
    subrank takes an adjacency dictionary in (nid, pids) format and returns a
    dictionary mapping nids to their SubRank.
    """
    # Needs a reversed graph.
    rev = dict([(nid, set()) for nid in adj])
    for cid in adj:
        for pid in adj[cid]:
            rev[pid].add(cid)

    progress = ProgressBar('Computing SubRank', maximum=len(rev))
    scoremap = {}
    size = float(len(rev))

    # Compute SubRank.
    for nid in rev:
        progress.next()

        queue = [nid]
        visited = set((nid,))

        # Breadth-first transitive closure.
        while queue:
            cid = queue.pop(0)
            for pid in rev[cid]:
                if pid not in visited:
                    queue.append(pid)
                    visited.add(pid)

        scoremap[nid] = len(visited) / size

    sys.stdout.write(' done.\n')
    sys.stdout.flush()

    return scoremap


def subrank2(adj):
    """
    subrank2 takes an adjacency dictionary in (nid, pids) format and returns a
    dictionary mapping nids to their SubRank. subrank2 is faster than subrank,
    but uses much more memory.
    """
    progress = ProgressBar('Computing SubRank')

    # Find leaves.
    pids = set()
    for nid in adj:
        pids.update(adj[nid])
    queue = list(set(adj).difference(pids))
    assert len(queue) != 0

    # BFS.
    scoremap = dict([(nid, set((nid,))) for nid in adj])
    while queue:
        progress.next()
        cid = queue.pop(0)
        for pid in adj[cid]:
            plen = len(scoremap[pid])
            scoremap[pid].update(scoremap[cid])
            if plen != len(scoremap[pid]) and pid not in queue: 
                queue.append(pid)

    sys.stdout.write(' done.\n')
    sys.stdout.flush()

    size = float(len(adj))
    scoremap = dict([(nid, len(scoremap[nid]) / size) for nid in scoremap])
    #scoremap1 = subrank(adj)
    #for nid in scoremap:
    #    if scoremap[nid] != scoremap1[nid]:
    #        print nid + ' ' + str(scoremap[nid]) + ' ' + str(scoremap1[nid])
    #        assert False

    return scoremap


def subrank3(adj):
    """
    subrank2 takes an adjacency dictionary in (nid, pids) format and returns a
    dictionary mapping nids to their SubRank. subrank3 uses BitStrings and the
    Warshall algorithm, so it is the most scalable python SubRank yet!
    """
    # Map adj to a reversed bitstring adjacency matrix, for speed.
    matrixmap = {}
    A = []
    for nid in adj:
        matrixmap[nid] = len(A)
        A.append(BitString(uint=0, length=len(adj)))

    for cid in adj:
        for pid in adj[cid]:
                A[matrixmap[pid]][matrixmap[cid]] = 1

    # Compute SubRank.
    progress = ProgressBar('Computing SubRank')

    T = A
    for j in xrange(len(adj)):
        progress.next()
        for i in xrange(len(adj)):
            if T[i][j]:
                T[i] = T[i]|T[j]

    sys.stdout.write(' done.\n')
    sys.stdout.flush()

    return dict([(nid, float(sum(T[matrixmap[nid]]) + 1) / len(adj)) for nid in adj])


def sizeof(adj, nid):
    """
    sizeof returns the size of nid's lineage in adj.
    """
    queue = [nid]
    visited = set()
    while queue:
        cid = queue.pop(0)
        if cid not in visited:
            visited.add(cid)
            queue.extend(adj[cid])

    return len(visited)


def truncate(adj, scoremap, nid, threshold):
    """
    truncate truncates an adjacency matrix in (nid, pids) format to a subgraph,
    given a scoremap, query nid, and threshold.
    """
    queue = [(0.0, nid)]
    visited = set()

    # Best-first traversal; get smaller scores first.
    while queue:
        (score, cid) = queue.pop(0)
        if cid not in visited:
            visited.add(cid)
            if score <= threshold:
                for i in [(scoremap[pid] - scoremap[cid], pid) for pid in adj[cid]]:
                    bisect.insort(queue, i)

    return visited


def plot(adj, scoremap, nid):
    """
    plot executes a series of "theoretical truncates" and returns an ordered
    (threshold, set_size) list.
    """
    threshold = 0.0
    queue = [(0.0, nid)]
    visited = set()
    ret = {}

    # Best-first traversal; get smaller scores first.
    while queue:
        (score, cid) = queue.pop(0)
        if cid not in visited:
            visited.add(cid)
            if score > threshold:
                set_size = len(visited.union(set([nid for (s, nid) in queue])))
                if set_size not in ret: ret[set_size] = threshold
                threshold = score
            for i in [(scoremap[pid] - scoremap[cid], pid) for pid in adj[cid]]:
                bisect.insort(queue, i)

    set_size = len(visited)
    if set_size not in ret: ret[set_size] = threshold
    return sorted([(threshold, set_size) for (set_size, threshold) in ret.items()])


def sample(adj, scoremap, nid):
    """
    sample executes a series of actual truncates at intervals across a range
    and returns a (threshold, set_size) list. An alternative to plot.
    """
    sample_range = 5.0
    num_samples = 100
    step = sample_range / num_samples

    ret = {}
    for i in xrange(num_samples):
        threshold = step * i
        set_size = len(truncate(adj, scoremap, nid, threshold))
        if set_size not in ret: ret[set_size] = threshold

    return sorted([(threshold, set_size) for (set_size, threshold) in ret.items()])


def analyze(adj, scoremap, nid):
    """
    analyze prints an analysis of the "best" threshold(s) in a plot.
    """
    p = plot(adj, scoremap, nid)

    # Find the "best" ratio set size increase.
    ratio = 0.0
    threshold = 0.0
    for i in xrange(0, len(p) - 1):
        if (p[i + 1][1] / p[i][1]) > ratio:
            ratio = p[i + 1][1] / p[i][1]
            threshold = (p[i + 1][0] + p[i][0]) / 2

    return threshold

"""
    # Find the largest order-of-magnitude threshold increase.
    magnitude = 0.0
    m_threshold = 0.0
    for i in xrange(1, len(p) - 1):
        if p[i + 1][0] / p[i][0] > magnitude:
            magnitude = p[i + 1][0] / p[i][0]
            m_threshold = (p[i + 1][0] + p[i][0]) / 2

    # Find the largest order-of-magnitude set size increase.
    magnitude = 0.0
    s_threshold = 0.0
    for i in xrange(0, len(p) - 1):
        if p[i + 1][1] / p[i][1] > magnitude:
            magnitude = p[i + 1][1] / p[i][1]
            s_threshold = (p[i + 1][0] + p[i][0]) / 2

    # Find the largest threshold below the challenge size.
    magnitude = 0
    c_threshold = 0.0
    for (threshold, set_size) in p:
        if magnitude <= set_size and set_size <= 52:
            magnitude = set_size
            c_threshold = threshold

    return (m_threshold, s_threshold, c_threshold)
"""


def evaluate(adj, scoremap, oracle, labels, leaves=False, maximum=None, testset=None):
    """
    evaluate evaluates up to maximum random queries against an oracle and
    compiles statistics.
    """
    # Statistics.
    set_sizes = {}
    diffs = {}
    ratios = {}
    avg_errors = {}
    max_errors = {}

    start = time.time()

    # Create the iterator.
    if testset is None: testset = adj.keys()
    if not leaves:
        pop = set(testset)
        for nid in testset:
            if len(adj[nid]) == 0: pop.discard(nid)
        if maximum is None: maximum = len(pop)
        niter = random.sample(pop, min(maximum, len(pop)))
    else:
        leaves = set(testset)
        for nid in testset:
            if len(adj[nid]) == 0: leaves.discard(nid)
            else: leaves.difference_update(adj[nid])
        if maximum is None: maximum = len(leaves)
        niter = random.sample(leaves, min(maximum, len(leaves)))

    # Run the eval.
    progress = ProgressBar('Evaluating', maximum=len(niter))
    for query in niter:
        progress.next()

        # Truncate, comparing our method and the oracle side-by-side.
        threshold = analyze(adj, scoremap, query)
        queue = [(0.0, None, query, None)]
        visited = set()
        o_visited = set()
        errors = []
        valid = not leaves

        # ALGORITHM: Run truncate and and the oracle as a BFS side-by-side.
        # At each BFS step, store the "error", which is defined as:
        #   None if neither truncate or the oracle has terminated.
        #   0 if truncate and the oracle terminate simultaneously.
        #   +1 for each step beyond the oracle truncate takes.
        #   -1 for each step beyond truncate the oracle takes.
        while queue:
            (score, cid, nid, error) = queue.pop()
            assert error != 0 # A zero error means both terminated, so...
            if nid in visited and nid in o_visited: continue

            # Figure out who's terminat(ing/ed).
            term = len(adj[nid]) == 0 or (error is not None and error < 0) or nid in visited or score > threshold
            o_term = len(adj[nid]) == 0 or (error is not None and error > 0) or nid in o_visited or oracle(query, cid, nid)
            if leaves and oracle(query, cid, nid): valid = True

            #if not len(adj[nid]) == 0 and not (error is not None and error < 0) and not nid in visited and score > threshold: print labels[nid]
            #if not len(adj[nid]) == 0 and not (error is not None and error > 0) and not nid in o_visited and oracle(query, cid, nid): print labels[nid]

            # nid only goes in the ret set if the relevant alg is still running
            if error is None or error > 0:
                visited.add(nid)
            if error is None or error < 0:
                o_visited.add(nid)

            # Figure out the next error to assign.
            if error is not None:
                error += 1 if error > 0 else -1
            elif (term or o_term):
                error = 0
                if term: error -= 1
                if o_term: error += 1

            # If an alg is still running do the next BFS step, else terminate.
            if not (term and o_term):
                for pid in adj[nid]:
                    bisect.insort(queue, (scoremap[pid] - scoremap[nid], nid, pid, error))
            else:
                assert error is not None
                errors.append(abs(error))

        # Collect stats.
        if valid:
            set_sizes[query] = (len(visited), len(o_visited), sizeof(adj, query))
            diffs[query] = abs(len(visited) - len(o_visited))
            ratios[query] = float(diffs[query]) / len(o_visited)
            avg_errors[query] = float(sum(errors)) / len(errors)
            max_errors[query] = max(errors)

    sys.stdout.write(' done.\n')
    sys.stdout.flush()

    print 'Time: ' + str(time.time() - start)
    print 'Average difference: ' + str(float(sum(diffs.values())) / len(diffs)) + ', worst: ' + max(diffs, key=diffs.get)
    print 'Average 95% diff: ' + str(float(sum(sorted(diffs.values())[:int(0.95 * len(diffs))])) / int(0.95 * len(diffs)))
    print 'Average ratio: ' + str(float(sum(ratios.values())) / len(ratios)) + ', worst: ' + max(ratios, key=ratios.get)
    print 'Average average error: ' + str(float(sum(avg_errors.values())) / len(avg_errors)) + ', worst: ' + max(avg_errors, key=avg_errors.get)
    print 'Average maximum error: ' + str(float(sum(max_errors.values())) / len(max_errors)) + ', worst: ' + max(max_errors, key=max_errors.get)

    #for line in set_sizes.values():
    #    print line
    #print min(set_sizes, key=lambda x: (abs(set_sizes[x][0] - set_sizes[x][1]), abs(set_sizes[x][2] - set_sizes[x][1])))
    return sorted(set_sizes.items(), key=lambda (query, (t_size, o_size, i_size)): (abs(t_size - o_size), abs(i_size - o_size)))
