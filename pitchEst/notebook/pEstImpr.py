import os, sys
import numpy as np
import math
import matplotlib.pyplot as plt

import essentia as ess
import essentia.standard as esstd

import pEstAssess as pa

def testImprovement(pool, pFunc, M=100, argv=''):
    names = np.append(pool['name'], '')
    pEsts = np.append(pool['lowLevel.pitch.median'], 0)
    pTags = np.append(pool['annotated_pitch'], 0)
    confs = np.append(pool['lowLevel.pitch_instantaneous_confidence.median'], 0);
    N = len(names)
   
    tag = np.zeros(M); oEst = np.zeros(M); iEst = np.zeros(M); 
    oConf = np.zeros(M); iConf = np.zeros(M); filenames = [];
    for m in range(M):
        i = np.random.randint(N)
        filename = names[i]
        print "file: "+filename
        loader = esstd.MonoLoader(filename = './sounds/all/'+filename);
        x = loader();
        
        ip, ic = pFunc((x, argv))
        
        
        pTag = pTags[i]
        pEst = pEsts[i] 

        ipEst = np.median(ip)
        iconf = np.median(ic)

        tag[m] = pTag;
        oEst[m] = pEst;
        iEst[m] = ipEst;
        oConf[m] = confs[i];
        iConf[m] = iconf;
        
        filenames.append(names[i])
        # remove sound from possible next sounds: 
        names = np.delete(names, i)
        pEsts = np.delete(pEsts, i)
        pTags = np.delete(pTags, i)
        confs = np.delete(confs, i)
        N = len(names)

    oErr = abs(tag - oEst)
    iErr = abs(tag - iEst)
   
    ost = pa.semitoneDist(tag, oEst)
    ist = pa.semitoneDist(tag, iEst)
 
    print "Improvement:\n\told mu: " + str(np.mean(abs(ost))) + " st\tnew mu: " + str(np.mean(abs(ist))) + " st"
    return filenames, tag, oEst, iEst, oConf, iConf


def incResolution_pYinFFT(argv):
    '''
        In some noisy signals a higher resulotion in the spectrogram can 
            increase the difference between the noisefloor and the harmonics.
        if the confidence of the pitchYinFFT algorithm is lower than the treshold (argv[1])
            the pYinFFT is recalculated with a higher resolution
    '''
    
    

def trimSilence(x, M=2048, H=1024):
    StrtStop = esstd.StartStopSilence();
    for frame in esstd.FrameGenerator(x, frameSize=M, hopSize=H):
        start, stop = StrtStop(frame)
    
    return x[start*H:stop*H]
 
def noSilence_pYinFFT(argv):
    x = argv[0]
    M = 2048
    H = 1024
 
    StrtStop = esstd.StartStopSilence();
    pYin = esstd.PitchYinFFT(frameSize=M);
    win = esstd.Windowing(size=M, type='blackmanharris62');
    spec =  esstd.Spectrum();
   
    N = len(x)
    frameC = int(N/M)
    pitch = np.array([]); conf = np.array([]);

    for fc in esstd.FrameGenerator(x, frameSize = M, hopSize = H):
        p, c = pYin(spec(win(fc)))
        pitch = np.append(pitch, p);
        conf = np.append(conf, c);
        srtStp = StrtStop(fc)

    start, stop = srtStp;

    pitch = pitch[start:stop];
    conf = conf[start:stop]
    return pitch, conf

def trimAttack(x, M, H):
    # instantiate algorithms:
    Env = esstd.Envelope();
    LogAttT = esstd.LogAttackTime();

    x = trimSilence(x, M, H) 
    env = Env(x)
    logattt = LogAttT(env)
       
    start_n = np.where(np.array(env * 1000, dtype=int) > 0)[0][0] 
    
    afterAtt = start_n + (10**logattt * 44100)
    x = x[afterAtt:]
    
    return x

def noAttack_pYinFFT(argv):
    x = argv[0]
    M = 2048
    H = 1024
    
    # instantiate algorithms:
    pYin = esstd.PitchYinFFT(frameSize=M)
    win = esstd.Windowing(size=M, type='blackmanharris62')
    spec = esstd.Spectrum();

    x = trimAttack(x, M, H)
    
    pitch = np.array([]); conf = np.array([])
    for fr in esstd.FrameGenerator(x, frameSize=M, hopSize=H):
        p, c = pYin(spec(win(fr)))
    
        pitch = np.append(pitch, p);
        conf = np.append(conf, c);
    return pitch, conf

def normalise(x):
    return x / float(np.max(abs(x)))
def removeFromPool(old_pool, strt, end):
    pool = ess.Pool()
    
    names = old_pool.descriptorNames()
    for name in names:
        print "Name: "+name
        vals = old_pool[name]
        if type(vals) != type("test"):    
            for i in range(strt):
                pool.add(name, vals[i])
            for i in range(end, len(vals)):
                pool.add(name, vals[i])
        else:
            pool.add(name, vals);
    return pool

def loadData():
    try:
        dataIn = esstd.YamlInput(filename='./results/descriptors_nomods.json')
        pool = dataIn();
    except:
        calcAll()
        pool = dataIn();
    return pool



