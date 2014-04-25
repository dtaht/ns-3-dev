import os
import sys

def jain(it):
    t = {}

    for line in it:
        l = line.split()
        try:
            if l[1] == '<->':
                t[l[0].split(':')[0]] = int(l[-1])
        except IndexError:
            pass

    n=sum(t.itervalues())**2
    d=(len(t)*sum(map(lambda x: x**2,t.itervalues())))
    return len(t), n/float(d)

for fn in sys.argv[1:]:
    n,j = jain(os.popen('tshark -z conv,tcp -q -r '+fn,'r'))
    print fn, n, j
