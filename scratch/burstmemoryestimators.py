import os
import os.path
import sys
from scapy.all import *
import numpy as np
import matplotlib.pyplot as plt
import itertools
import math
import json

def burstest(fn,tau,time=False):
    packets = rdpcap(fn)
    reader = ((p.time, PPP(str(p))) for p in iter(packets))
    filtered = ((t, pkt) for t, pkt in reader if
                TCP in pkt and
                (pkt[TCP].dport == 50000))
    tsl = None
    tdelta = 0
    tdeltal = 0
    dev = 0
    av = 0
    avl = 0
    ssq = 0
    sd = 1
    sdl = 1
    m = 0
    res = []
    w = tau
    for ts, pkt in filtered:
        #print pkt.summary()
        if tsl is not None:
            tdelta = ts - tsl
            if time:
                w = 1-math.exp(-tdelta/tau)
            dev = tdelta - av
            av = av + w*dev
            ssq = (1-w)*ssq + dev*(tdelta-av)
            sd = math.sqrt((ssq*w*(2-w))/(2*(1-w)))
            b = (sd-av)/(sd+av)
            m = (1-w)*m + w*(tdelta-av)*(tdeltal-avl)/(sd*sdl)
            res.append((ts, tdelta, av, sd, b, m))
        tsl = ts
        tdeltal = tdelta
        avl = av
        sdl = sd
    res = np.array(res)
    deltas = res[:,1]
    sddel = np.std(deltas)
    mdel = np.mean(deltas)
    ti=deltas[:-1]
    til=deltas[1:]
    mti=np.mean(ti)
    best = np.mean(res[:,4])
    b = (sddel - mdel)/(sddel + mdel)
    mtil=np.mean(til)
    mem = np.sum((ti-mti)*(til-mtil))/(np.std(ti)*np.std(til)*ti.shape[0])
    return res[:,0], res[:,1], res[:,2], res[:,3], res[:,4], res[:,5], best, b, mem

if __name__ == '__main__':
    
    case = json.load(open(os.path.join(sys.argv[1],'case.json'),'r'))
    print case
    args = [i for i in os.listdir(sys.argv[1]) if i.endswith('.pcap') and 'Left' in i]
    # sort by interface ID
    args.sort(key=lambda s: int(s.split('-')[-1].split('.')[0]))
    # last one is the output, don't want to plot that
    args = args[:-1]
    nrows = len(args)
    for n,p in zip(args, range(0,nrows+1)):
        print p, n, nrows, p+nrows*3
        n = os.path.join(sys.argv[1],n)
        t, ival, mi, sdi, brsti, memi, best, b, mem = burstest(n,0.1)
        plt.subplots_adjust(wspace=0.15, hspace=0.15, left=0.05, right=0.97, top=0.97, bottom=0.05)
        plt.subplot(nrows, 3, 3*p+1)
        plt.grid(True)
        plt.tick_params(labelsize='x-small')
        plt.locator_params(axis='y', nbins=4, prune='lower')
        #plt.ylim(0,0.5)
        plt.xlim(0,64)
        plt.plot(t, ival, 'b.')#, t, mi, 'r.', t, sdi, 'g.')
        plt.subplot(nrows, 3, 3*p+2)
        plt.grid(True)
        plt.tick_params(labelsize='x-small')
        plt.ylim(-1,1)
        plt.xlim(0,64)
        plt.plot(t, brsti, 'r-', t, memi, 'g-')
        plt.subplot(nrows, 3, 3*p+3)
        plt.grid(True)
        plt.tick_params(labelsize='x-small')
        plt.xlim(0,0.1)
        x = np.sort(ival)
        n = len(x)
        x2 = np.repeat(x, 2)
        y2 = np.hstack([0.0, np.repeat(np.arange(1,n) / float(n), 2), 1.0])
        plt.plot(x2, y2)
        print best, b, mem
    plt.show()
