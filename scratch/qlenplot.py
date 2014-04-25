import os
import sys
import re
import matplotlib.pyplot as plt
import numpy as np
import itertools

#1.14783s TcpServer:bytesInQueueTrace(): Queue went from 426624 to 425182 (-1442)
qex = re.compile('([0-9.]+)s (\d+).*to (\d+)')
#1.14783s CoDelQueue:ShouldDrop(): Sojourn time 0.0513604
sjex = re.compile('([0-9.]+)s (\d+).*Sojourn time ([0-9.e-]+)')

def qplot(it,rex):
    qs=[]
    sjs=[]
    for line in it:
        qm = rex.search(line)
        if qm is not None:
            yield int(qm.group(2)), float(qm.group(1)), float(qm.group(3))

plotnum=1
for fn in sys.argv[1:]:
    t = np.array(list(qplot(open(fn,'r'), qex)))
    s = np.array(list(qplot(open(fn,'r'), sjex)))
    nodes = set(t[:,0])
    print nodes, np.shape(t), np.shape(s), t, s

    for n in nodes:
        plt.subplot(2,len(nodes),plotnum)
        print np.shape(np.equal(t[:,0],n))
        plt.plot(np.compress(np.equal(t[:,0],n),t[:,1], axis=0), 
                 np.compress(np.equal(t[:,0],n),t[:,2], axis=0),'r')
        plt.subplot(2,len(nodes),plotnum+1)
        plt.plot(np.compress(np.equal(s[:,0],n),s[:,1], axis=0), 
                 np.compress(np.equal(s[:,0],n),s[:,2], axis=0),'r')
        plotnum += 2
plt.show()
