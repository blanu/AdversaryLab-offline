import os

import json
import logging

from random import choice
import numpy
from numpy.random import normal, poisson, exponential, multinomial
from scipy.stats import norm, expon

def save(model, path):
  bs=json.dumps(model)
  f=open(path, 'w')
  f.write(bs)
  f.close()

def checkFitLengthModel(model, stats):
  sampleSize=1000
  bounds=[1,1440]
  countsA=generateNormalCounts(model, sampleSize, bounds)
  countsB=generateBootstrapCounts(stats, sampleSize, bounds)
  return compareCounts(countsA, countsB)

def checkFitContentModel(model, stats):
  sampleSize=1000
  bounds=[0,255]
  countsA=generateMultinomialCounts(model, sampleSize, bounds)
  countsB=generateBootstrapCounts(stats, sampleSize, bounds)
  return compareCounts(countsA, countsB)

def checkFitEntropyModel(model, stats):
  sampleSize=1000
  samplesA=generateNormalSamples(model, sampleSize)
  samplesB=generateBootstrapSamples(stats, sampleSize)
  return compareSamples(samplesA, samplesB)

def checkFitFlowModel(model, stats):
  sampleSize=1000
  statlist=[]
  for stat in stats:
    statlist.append(stat)
  samples=generatePoissonSamples(model, len(statlist), sampleSize)
  return compareSamples(samples, statlist)

def checkFitDurationModel(model, stats):
  lam=model['params'][0]
  e=expon(scale=1.0/lam)
  fits=[]
  for sample in stats:
    fits.append(e.pdf(sample))
  return fits

def generateMultinomialCounts(model, sampleSize, bounds):
  dist=model['params']
  return list(multinomial(sampleSize, list(dist)))

def generateNormalCounts(model, sampleSize, bounds):
  mean=model['params'][0]
  sd=model['params'][1]
  size=bounds[1]-bounds[0]
  counts=[0]*size
  samples=normal(mean, sd, sampleSize)
  for sample in samples:
    if sample>bounds[0] and sample<bounds[1]:
      index=int(sample-bounds[0])
      counts[index]=counts[index]+1
  return counts

def generateNormalSamples(model, sampleSize):
  mean=model['params'][0]
  sd=model['params'][1]
  return normal(mean, sd, sampleSize)

def generatePoissonSamples(model, numSlots, sampleSize):
  l=model['params'][0]
  samples=[]
  for slot in range(numSlots):
    samples.append(poisson(l, sampleSize))
  return samples

def generateExponentialSamples(model, sampleSize):
  beta=model['params'][0]
  return exponential(beta, sampleSize)

def generateBootstrapCounts(stats, sampleSize, bounds):
  size=(bounds[1]-bounds[0])+1
  counts=[0]*size
  samples=[]
  for x in range(sampleSize):
    samples.append(choice(stats))
  for sample in samples:
    if sample>bounds[0] and sample<bounds[1]:
      index=sample-bounds[0]
      counts[index]=counts[index]+1
  return counts

def generateBootstrapSamples(stats, sampleSize):
  samples=[]
  for x in range(sampleSize):
    samples.append(choice(stats))
  return samples

def compareCounts(countsA, countsB):
  e=0
  size=len(countsA)
  for x in range(size):
    a=countsA[x]
    b=countsB[x]
    e=e+rmse(a,b)
  return e

def compareSampleSets(setA, setB):
  e=0
  size=len(setA)
  for x in range(size):
    samplesA=setA[x]
    samplesB=setB[x]
    for y in range(len(samplesA)):
      a=samplesA[y]
      b=samplesB[y]
      e=e+rmse(a,b)
  return e

def compareSamples(samplesA, samplesB):
  e=0
  size=len(samplesA)
  for x in range(size):
    a=samplesA[x]
    b=samplesB[x]
    e=e+rmse(a,b)
  return e

def rmse(predictions, targets):
  return numpy.sqrt(numpy.mean((predictions - targets) ** 2))

class ConnStats:
  def __init__(self):
    length=[] # by packet
    entropy=[] # by packet
    flow=[] # whole connection, by millisecond
    content=[] # whole connection, counts by byte
    duration=0 # whole connection

def checkModels(models):
  for x in range(len(models)):
    model=models[x]
    if not checkModel(model):
      logging.error("Bad model %d %s" % (x, str(model)))
      return False

def checkModel(model):
  if not model.duration or not model.duration.distribution:
    return False
  elif not model.flow or not model.flow.distribution:
    False
  elif not model.length or not model.length.distribution:
    False
  elif not model.entropy or not model.entropy.distribution:
    False
  elif not model.content or not model.content.distribution:
    False
  else:
    return True

def testAdversary(adversary, model, positive, negative):
  logging.info('testAdversary')
  fits={positive: [], negative: []}
  for dataset in os.listdir('conns'):
    print('Testing dataset %s' % (dataset))
    for side in [positive, negative]:
      print('Testing protocol %s / %s' % (dataset, side))
      if os.path.exists('conns/'+dataset+'/'+side):
        for pcap in os.listdir('conns/'+dataset+'/'+side):
          print('Testing pcap %s / %s / %s' % (dataset, side, pcap))
          for connfile in os.listdir('conns/'+dataset+'/'+side+'/'+pcap):
            print('Testing connection %s / %s / %s / %s' % (dataset, side, pcap, connfile))
            conn=load('conns/'+dataset+'/'+side+'/'+pcap+'/'+connfile)
            connfit={}
            for sidename in ['positive', 'negative']:
              fit={'incoming': {}, 'outgoing': {}}
              if conn['duration']==0:
                fit['duration']=0
              else:
                fit['duration']=checkFitDurationModel(model[sidename]['duration'], [conn['duration']])

              for direction in ['incoming', 'outgoing']:
                fit[direction]['content']=float(checkFitContentModel(model[sidename][direction+'Model']['content'], conn[direction+'Stats']['content']))
                fit[direction]['length']=float(checkFitLengthModel(model[sidename][direction+'Model']['lengths'], conn[direction+'Stats']['lengths']))
                fit[direction]['entropy']=float(checkFitEntropyModel(model[sidename][direction+'Model']['entropy'], [conn[direction+'Stats']['entropy']]))
                fit[direction]['flow']=float(checkFitFlowModel(model[sidename][direction+'Model']['flow'], conn[direction+'Stats']['flow']))

              connfit[sidename]=fit

            fits[side].append(connfit)

  save(fits, 'tests/'+adversary)

def score(fits, label):
  size=len(fits)
  if size==0:
    logging.error('Error, no fit data to score')
    return 0
  else:
    count=0
    for fit in fits:
      if (label and fit>0) or (not label and fit<0):
        count=count+1
    return float(count)/float(size)

def load(path):
  f=open(path)
  bs=f.read()
  f.close()
  return json.loads(bs)

if not os.path.exists('tests'):
  os.mkdir('tests')
ads=os.listdir('adversaries')
for ad in ads:
  model=load('adversaries/'+ad+'/'+'model')
  parts=ad.split('-')
  positive=parts[0]
  negative=parts[1]
  testAdversary(ad, model, positive, negative)
