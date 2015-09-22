import os
import sys

import json
import yaml
import logging
import math

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
  model=model['params']
  stats=stats[:1440]
  fit=0
  for index in range(len(stats)):
    score=model[index]*stats[index]
    fit=fit+score
  return fit
#  countsA=generateMultinomialCounts(model, sampleSize, bounds)
#  countsB=generateBootstrapCounts(stats, sampleSize, bounds)
#  return compareCounts(countsA, countsB)

def checkFitContentModel(model, stats):
  # sampleSize=1000
  # bounds=[0,255]
  # countsA=generateMultinomialCounts(model, sampleSize, bounds)
  # countsB=generateBootstrapCounts(stats, sampleSize, bounds)
  # return compareCounts(countsA, countsB)

  model=model['params']
  stats=stats[:256]
  fit=0
  for index in range(len(stats)):
    score=model[index]*stats[index]
    fit=fit+score
  return fit

def checkFitEntropyModel(model, stats):
#  sampleSize=1000
#  samplesA=generateNormalSamples(model, sampleSize)
#  samplesB=generateBootstrapSamples(stats, sampleSize)
#  return compareSamples(samplesA, samplesB)
  m=model['params'][0]
  sd=model['params'][1]
  n=norm(m, sd)
  fit=0
  for index in range(len(stats)):
    score=n.pdf(stats[index])
    fit=fit+score
  return fit

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
  return numpy.mean(fits)

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

def checkFitSequence(sequence, first):
  if len(sequence) > len(first):
    return 0

  for x in range(len(sequence)):
    if first[x]!=chr(sequence[x]):
      return 0

  return 1

def testAdversary(adversary, model, positive, negative, feature, training, testing):
  logging.info('testAdversary')
  fits={positive: [], negative: []}
  for side in [positive, negative]:
    if os.path.exists(testing+'/'+side):
      for pcap in os.listdir(testing+'/'+side):
        conn=load(testing+'/'+side+'/'+pcap)
        connfit={}
        for sidename in ['positive', 'negative']:
          connid=side+'-'+pcap
          fit={connid: {'incoming': {}, 'outgoing': {}}}
          if conn['duration']==0:
            fit[connid]['duration']=0
          else:
            fit[connid]['duration']=checkFitDurationModel(model[sidename]['duration'], [conn['duration']])

          for direction in ['incoming', 'outgoing']:
            if feature=='content':
              fit[connid][direction]['content']=float(checkFitContentModel(model[sidename][direction+'Model']['content'], conn[direction+'Stats']['content']))
            if feature=='length':
#                  print(model[sidename][direction+'Model']['length'])
#                  print(conn[direction+'Stats'].keys())
              fit[connid][direction]['length']=float(checkFitLengthModel(model[sidename][direction+'Model']['length'], conn[direction+'Stats']['lengths']))
            if feature=='entropy':
              fit[connid][direction]['entropy']=float(checkFitEntropyModel(model[sidename][direction+'Model']['entropy'], [conn[direction+'Stats']['entropy']]))
            if feature=='flow':
              fit[connid][direction]['flow']=float(checkFitFlowModel(model[sidename][direction+'Model']['flow'], conn[direction+'Stats']['flow']))

          connfit[sidename]=fit

        fits[side].append(connfit)

  save(fits, 'split-tests/'+adversary+'-'+feature+'-'+training+'-'+testing)

def testAdversarySequence(adversary, model, positive, negative):
  logging.info('testAdversarySequence')
  fits={positive: [], negative: []}
  for dataset in os.listdir('first'):
    print('Testing dataset %s' % (dataset))
    for protocol in [positive, negative]:
      if os.path.exists('first/'+dataset+'/'+protocol):
        for pcap in os.listdir('first/'+dataset+'/'+protocol):
          for conn in os.listdir('first/'+dataset+'/'+protocol+'/'+pcap):
            connfit={}
            for sidename, side in [('positive', positive), ('negative', negative)]:
              connid=dataset+'-'+protocol+'-'+pcap+'-'+conn
              fit={connid: {'incoming': {}, 'outgoing': {}}}
              for direction in ['incoming', 'outgoing']:
                if os.path.exists('first/'+dataset+'/'+protocol+'/'+pcap+'/'+conn+'/'+direction):
                  first=loadData('first/'+dataset+'/'+protocol+'/'+pcap+'/'+conn+'/'+direction)
                  fit[connid][direction]['sequence']=float(checkFitSequence(model[sidename][direction+'Model']['sequence'], first))
              connfit[sidename]=fit
            fits[protocol].append(connfit)

  print('Saving sequence tests %d' % (len(fits[positive])))
  save(fits, 'tests/'+adversary+'-sequence')

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

def loadData(path):
  f=open(path)
  bs=f.read()
  f.close()
  return bs

def load(path):
  f=open(path)
  bs=f.read()
  f.close()
  return json.loads(bs)

def loadYaml(path):
  f=open(path)
  bs=f.read()
  f.close()
  return yaml.load(bs)

if not os.path.exists('split-tests'):
  os.mkdir('split-tests')
ads=os.listdir('models')
for ad in ads:
  if os.path.exists('models/'+ad+'/'+'features'):
    features=loadYaml('models/'+ad+'/'+'features')
  else:
    features=loadYaml('features.all')    
  parts=ad.split('-')
  positive=parts[0]
  negative=parts[1]
  for training in ['training', 'testing']:
    for testing in ['training', 'testing']:
      model=load('models/'+ad+'/'+training+'-model')
      for feature in features:
        print('Testing feature '+feature)
        if feature=='sequence':
          print('Skipping sequence for now...')
          pass
#          testAdversarySequence(ad, model, positive, negative)
        else:
          if not os.path.exists('split-tests/'+ad+'-'+feature+'-'+training+'-'+testing):
            testAdversary(ad, model, positive, negative, feature, training, testing)
