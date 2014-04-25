import os
import os.path
import sys
import shlex
import time
import traceback
import itertools
from pprint import pprint
from subprocess import call, check_call, check_output, CalledProcessError, STDOUT
from multiprocessing import Pool, cpu_count
import json


def runex(args):
    try:
        t = time.time()
        A = args
        c = 'tcp-qfp '+' '.join(['--{0}={1}'.format(*it) for it in A.items()])
        d = 'results/'+c.replace(' ','-').replace('---','-').replace('=','+')
        try:
            os.mkdir(d)
        except OSError:
            pass
        print d
        print c
        out=check_output('LD_LIBRARY_PATH=../../build ../../build/scratch/'+c, 
                         shell=True, stderr=STDOUT, cwd=d)
        with open(d+'/tcp-qfp.out','w') as f:
            f.write(out)
        with open(d+'/case.json','w') as j:
            j.write(json.dumps(args)+'\n')
        try:
            check_output('python ../../src/flow-monitor/examples/flowmon-parse-results.py tcp-qfp.flowmon > tcp-qfp-flowmon.out', 
                         shell=True, stderr=STDOUT, cwd=d)
        except:
            pass
    except:
        return "Process for %s threw an exception\n%s" % (repr(args),traceback.format_exc())
    return "Process for %s returned in %ds" % (repr(args), time.time()-t)

if __name__ == '__main__':
    R = 36
    R2 = 4
    expts = []
    n = 50
    defaults = {'Q1Type':'CoDel',
                'Q2Type':'CoDel',
                'maxBytes':'0',
                'writeFlowMonitor':'1',
                'nNodes':'100',
                'mNodes':'45',
                'Runtime':'60'
                }
    '''
User Arguments:
    --pathOut: Path to save results from --writeForPlot/--writePcap/--writeFlowMonitor
    --writeFlowMonitor: <0/1> to enable Flow Monitor and write their results
    --maxBytes: Total number of bytes for application to send
    --queueType: Set Queue type to CoDel, DropTail, RED, or SFQ
    --modeBytes: Set RED Queue mode to Packets <0> or bytes <1>
    --stack: Set TCP stack to NSC <0> or linux-2.6.26 <1> (warning, linux stack is really slow in the sim)
    --modeGentle: Set RED Queue mode to standard <0> or gentle <1>
    --maxPackets: Max Packets allowed in the queue
    --Quantum: SFQ and fq_codel quantum
    --nNodes: Number of client nodes
    --mNodes: Number of low latency client noodes
    --R: Bottleneck rate
    --R1: Low latency node edge link bottleneck rate
    --Q1Type: Set Queue type to DropTail or RED
    --Q1redMinTh: RED queue minimum threshold (packets)
    --Q1redMaxTh: RED queue maximum threshold (packets)
    --Q1maxPackets: Max Packets allowed in the queue
    --R2: High latency node edge link bottleneck rate
    --Q2Type: Set Queue type to DropTail or RED
    --Q2redMinTh: RED queue minimum threshold (packets)
    --Q2redMaxTh: RED queue maximum threshold (packets)
    --Q2maxPackets: Max Packets allowed in the queue
    --redMinTh: RED queue minimum threshold (packets)
    --redMaxTh: RED queue maximum threshold (packets)
    --SFQHeadMode: New SFQ flows go to the head
    --Interval: CoDel algorithm interval
    --Target: CoDel algorithm target queue delay
    '''
    cases = itertools.product([1.8,2.0],
        #(1.+(1.*r)/n for r in range(0,n+1)),
                              iter([#{'queueType':'CoDel',
                                    # 'Q1Type':'CoDel',
                                    # 'Q2Type':'CoDel'},
                                    #{'queueType':'DropTail',
                                    # 'maxPackets':'1000'},
                                    {'queueType':'fq_codel',
                                     'Quantum':'4500',
                                     'Q1Type':'CoDel',
                                     'Q2Type':'CoDel'},
                                    #{'queueType':'fq_codel',
                                    # 'Quantum':'1500',
                                    # 'Q1Type':'CoDel',
                                    # 'Q2Type':'CoDel'},
                                    #{'queueType':'fq_codel',
                                    # 'Quantum':'9000',
                                    # 'Q1Type':'CoDel',
                                    # 'Q2Type':'CoDel'},
                                    {'queueType':'fq_codel',
                                     'Quantum':'256',
                                     'Q1Type':'CoDel',
                                     'Q2Type':'CoDel'},
                                    ]),
                              iter([1]))
    for R1,Q,run in cases:
        print R1, Q, run
        D = dict(defaults)
        D.update({'R':'%fMbps'%R, 
                  'R1':'%fMbps'%R1, 
                  'R2':'%fMbps'%R2,
                  'RngRun':'%d'%run})
        D.update(Q)
        expts.append(D)
    pprint(expts)
    ncores = cpu_count()
    print "There are", len(expts), "cases, run time should be about", 21.*len(expts)/(ncores*60.), 'minutes'
    #sys.exit(0)
    pool = Pool(processes=ncores)
    result = pool.map(runex, expts)
    for o in result:
        print o


