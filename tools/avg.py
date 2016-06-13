#!/usr/bin/python
import sys

def main(datfile):
    datfile = open(datfile, 'r')
    avgdiff = 0
    avgmax = 0
    cnt = 0
    for line in datfile:
        (nid, tlen, olen, ilen, diff, maxerror) = line.split()
        avgdiff += int(diff)
        avgmax += int(maxerror)
        cnt += 1
    avgdiff = float(avgdiff) / cnt
    avgmax = float(avgmax) / cnt
    print str(avgdiff) + ' ' + str(avgmax)

if __name__ == '__main__':
    main(sys.argv[1])
