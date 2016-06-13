#!/usr/bin/python
import optparse
import os.path
import re


def truncdot(filename, head=None, tail=None):
    """truncdot truncates a .dot file given a head and/or tail."""
    # Sanity check.
    if (head is None and tail is None) or \
       (head is not None and tail is not None and tail < head):
        return

    postfix = '-'
    if head is not None: postfix += 'H' + str(head)
    if tail is not None: postfix += 't' + str(tail)

    dotfile = open(filename, 'r')
    truncfile = open(os.path.splitext(filename)[0] + postfix + '.dot', 'w')

    for line in dotfile:
        # Match edge.
        if re.match(r'^[0-9]+ -> [0-9]', line):
            (u, arrow, v, attr) = line.split(' ', 3)
            if (head is None or (head <= int(u) and head <= int(v))) and \
               (tail is None or (int(u) <= tail and int(v) <= tail)):
                truncfile.write(line)
        # Match node.
        elif re.match(r'^[0-9]+', line):
            (u, attr) = line.split(' ', 1)
            if (head is None or head <= int(u)) and \
               (tail is None or int(u) <= tail):
                truncfile.write(line)
        else:
            truncfile.write(line)

    dotfile.close()
    truncfile.close()


def parse_args():
    """parse_args parses sys.argv for truncdot."""
    # Help Menu
    parser = optparse.OptionParser(usage='%prog [options] dotfile')
    parser.add_option('-H', '--head',
                      type='int', dest='head', default=None,
                      help='start from rvstartid HEAD', metavar='HEAD')
    parser.add_option('-t', '--tail',
                      type='int', dest='tail', default=None,
                      help='end at rvstartid TAIL', metavar='TAIL')

    (opts, args) = parser.parse_args()

    truncdot(args[0], head=opts.head, tail=opts.tail)


if __name__ == '__main__':
    parse_args()
