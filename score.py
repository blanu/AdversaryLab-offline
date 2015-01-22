import os

import json
import logging

from random import choice
import numpy
from numpy.random import normal, poisson, exponential, multinomial

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
  sampleSize=1000
  samplesA=generateExponentialSamples(model, sampleSize)
  samplesB=generateBootstrapSamples(stats, sampleSize)
  return compareSamples(samplesA, samplesB)

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

def applyLabel(score, positive, negative):
  if score > 0:
    return positive
  elif score < 0:
    return negative
  else:
    return 'Unknown'

def finalScore(test, labels, positive, negative):
  logging.info('finalScore')
  final={}
  for side in [positive, negative]:
    conns=labels[side]
    total=0.0
    count=0.0
    for conn in conns:
      total=total+1
      if conn==side:
        count=count+1
    final[side]=count/total
  save(final, 'scores/final-'+test)

def labelScores(test, sums, positive, negative):
  logging.info('labelScores')
  labels={positive: [], negative: []}
  for side in [positive, negative]:
    conns=sums[side]
    for conn in conns:
      score={}
      score['duration']=applyLabel(conn['duration'], positive, negative)
      score['incoming']=applyLabel(conn['incoming'], positive, negative)
      score['outgoing']=applyLabel(conn['outgoing'], positive, negative)
      labels[side].append(score)
  save(labels, 'scores/labels-'+test)

def labelTotals(test, totals, positive, negative):
  logging.info('labelTotals')
  labels={positive: [], negative: []}
  for side in [positive, negative]:
    conns=totals[side]
    for conn in conns:
      label=applyLabel(conn, positive, negative)
      labels[side].append(label)
  save(labels, 'scores/decisions-'+test)
  finalScore(test, labels, positive, negative)

def totalScores(test, sums, positive, negative):
  logging.info('totalScores')
  totals={positive: [], negative: []}
  for side in [positive, negative]:
    conns=sums[side]
    for conn in conns:
      score=conn['duration']+conn['incoming']+conn['outgoing']
      totals[side].append(score)
  save(totals, 'scores/total-'+test)

  labelTotals(test, totals, positive, negative)

def sumScores(test, scores, positive, negative):
  logging.info('sumScores')
  sums={positive: [], negative: []}
  for side in [positive, negative]:
    conns=scores[side]
    for conn in conns:
      score={}
      score['duration']=conn['duration']
      score['incoming']=sumSide(conn['incoming'])
      score['outgoing']=sumSide(conn['outgoing'])
      sums[side].append(score)
  save(sums, 'scores/sum-'+test)

  labelScores(test, sums, positive, negative)
  totalScores(test, sums, positive, negative)

def sumSide(side):
  score=0
  for feature in ['content', 'flow', 'length', 'entropy']:
    score=score+side[feature]
  return score

def saveScores(scores):
  for protocol in scores:
    path='scores/raw-'+protocol+'.csv'
    f=open(path, 'w')
    f.write("duration incomingContent incomingEntropy incomingLength incomingFlow outgoingContent outgoingEntropy outoingLength outgoingFlow\n")
    items=scores[protocol]
    for item in items:
      data=[item['duration']]
      for side in ['incoming', 'outgoing']:
        for feature in ['content', 'entropy', 'length', 'flow']:
          data.append(item[side][feature])
      f.write(' '.join(map(str, data))+"\n")
    f.close()

def saveFits(scores):
  for protocol in scores:
    path='scores/fit-'+protocol+'.csv'
    f=open(path, 'w')
    for side in ['positive', 'negative']:
      f.write(side+"Duration ")
      for direction in ['Incoming', 'Outgoing']:
        for feature in ['Content', 'Entropy', 'Length', 'Flow']:
          f.write(side+direction+feature)
          f.write(' ')
    f.write("\n")
    items=scores[protocol]
    for item in items:
      data=[]
      for side in ['positive', 'negative']:
        data.append(item[side]['duration'])
        for direction in ['incoming', 'outgoing']:
          for feature in ['content', 'entropy', 'length', 'flow']:
            data.append(item[side][direction][feature])
      f.write(' '.join(map(str, data))+"\n")
    f.close()

def scoreAdversary(test, fits, positive, negative):
  logging.info('scoreAdversary')
  scores={positive: [], negative: []}
  for side in [positive, negative]:
    conns=fits[side]
    for conn in conns:
      score={}
      score['duration']=conn['negative']['duration']-conn['positive']['duration']
      for direction in ['incoming', 'outgoing']:
        score[direction]={}
        for feature in ['content', 'flow', 'length', 'entropy']:
          score[direction][feature]=conn['negative'][direction][feature]-conn['positive'][direction][feature]
      scores[side].append(score)
  save(scores, 'scores/raw-'+test)
  saveScores(scores)

  sumScores(test, scores, positive, negative)

def load(path):
  f=open(path)
  bs=f.read()
  f.close()
  return json.loads(bs)

if not os.path.exists('scores'):
  os.mkdir('scores')
tests=os.listdir('tests')
for test in tests:
  fits=load('tests/'+test)
  parts=test.split('-')
  positive=parts[0]
  negative=parts[1]
  saveFits(fits)
  scoreAdversary(test, fits, positive, negative)
