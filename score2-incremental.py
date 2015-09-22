import os
import sys

import json
import yaml
import logging

from random import choice
import numpy
from numpy.random import normal, poisson, exponential, multinomial

def sum(items):
  total=0
  for item in items:
    total=total+item
  return total

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

def labelScores(test, sums, positive, negative, features):
  logging.info('labelScores')
  labels={positive: [], negative: []}
  for side in [positive, negative]:
    conns=sums[side]
    for conn in conns:
      score={}
      if 'duration' in features:
        score['duration']=applyLabel(conn['duration'], positive, negative)
      for feature in features:
        if feature=='duration':
          continue
        directions=features[feature]
        for direction in directions:
          if direction in conn:
            score[direction]=applyLabel(conn[direction], positive, negative)
      labels[side].append(score)
  save(labels, 'scores/labels-'+test)

def labelTotals(test, totals, positive, negative, feature):
  logging.info('labelTotals')
  labels={positive: [], negative: []}
  for side in [positive, negative]:
    conns=totals[side]
    for conn in conns:
      label=applyLabel(conn, positive, negative)
      labels[side].append(label)
  save(labels, 'scores/decisions-'+test)
  finalScore(test, labels, positive, negative)

def totalScores(test, sums, positive, negative, features):
  logging.info('totalScores')
  totals={positive: [], negative: []}
  for side in [positive, negative]:
    conns=sums[side]
    for conn in conns:
      if 'duration' in features:
        score=conn['duration']

      for feature in features:
        if feature=='duration':
          continue
        score=0
        for direction in features[feature]:
          if direction in conn:
            score=score+conn[direction]
      totals[side].append(score)
  save(totals, 'scores/total-'+test)

  labelTotals(test, totals, positive, negative, feature)

def sumScores(test, scores, positive, negative, features):
  logging.info('sumScores')
  sums={positive: [], negative: []}
  for side in [positive, negative]:
    conns=scores[side]
    for conn in conns:
      score={}
      if 'duration' in features:
        score['duration']=conn['duration']
      for feature in features:
        if feature=='duration':
          continue
        for direction in features[feature]:
          if direction in conn:
            score[direction]=sumSide(conn[direction], feature)
      sums[side].append(score)
  save(sums, 'scores/sum-'+test)

  labelScores(test, sums, positive, negative, features)
  totalScores(test, sums, positive, negative, features)

def sumSide(side, feature):
  score=0
  try:
    score=score+side[feature]
  except:
    pass
  return score

def saveScores(scores, test, feature):
  for protocol in scores:
    path='scores/raw-'+test+'-'+protocol+'-'+feature+'.csv'
    f=open(path, 'w')
    if feature=='duration':
      f.write(feature+"\n")
    else:
      f.write(feature+"Incoming "+feature+"Outgoing\n")
    items=scores[protocol]
    for item in items:
      if feature=='duration':
        data=[item['duration']]
      else:
        data=[]
        for side in ['incoming', 'outgoing']:
          try:
            data.append(item[side][feature])
          except:
            continue
      f.write(' '.join(map(str, data))+"\n")
    f.close()

def saveFits(scores, test, features):
  for protocol in scores:
    path='scores/fit-'+test+'-'+protocol+'.csv'
    f=open(path, 'w')
    print("%d features" % (len(features)))
    for side in ['positive', 'negative']:
      if 'duration' in features:
        f.write(side+"Duration ")
      for feature in features:
        if feature=='duration':
          continue
        for direction in features[feature]:
          f.write(side+direction+feature)
          f.write(' ')
    f.write("\n")
    items=scores[protocol].values()
    for item in items:
      data=[]
      for side in ['positive', 'negative']:
        if 'duration' in features:
          data.append(item[side]['duration'])
        for feature in features:
          if feature=='duration':
            continue

          for direction in features[feature]:
            try:
              data.append(item[side][direction][feature])
            except Exception as e:
              print("Exception")
              print(e)
              data.append("NA")
      print("%d items" % (len(data)))
      f.write(' '.join(map(str, data))+"\n")
    f.close()

def saveAdjusted(adjusted, test, feature):
  for protocol in adjusted:
    path='scores/adjusted-'+test+'-'+protocol+'-'+feature+'.csv'
    f=open(path, 'w')
    if feature=='duration':
      f.write("Duration ")
    else:
      for direction in ['Incoming', 'Outgoing']:
        f.write(direction+feature)
        f.write(' ')
    f.write("\n")
    items=adjusted[protocol]
    for item in items:
      data=[]
      if feature=='duration':
        data.append(item['duration'])
      else:
        for direction in ['incoming', 'outgoing']:
          data.append(item[feature][direction])
      f.write(' '.join(map(str, data))+"\n")
    f.close()

def scoreAdversary(test, fits, positive, negative, features):
  logging.info('scoreAdversary')
  scores={positive: [], negative: []}
  for side in [positive, negative]:
    print('Scoring side '+side)
    conns=fits[side]
    for conn in conns.values():
      score={}
      if 'duration' in features:
        score['duration']=conn['positive']['duration']-conn['negative']['duration']
      for feature in features:
        if feature=='duration':
          continue

        print('Scoring '+feature)
        for direction in features[feature]:
          score[direction]={}
          try:
            score[direction][feature]=conn['positive'][direction][feature]-conn['negative'][direction][feature]
          except Exception as e:
            print('Error')
            print(e)
            continue
#            if feature=='length' and score[direction][feature]<0.001:
#              score[direction][feature]=0 # Too close to call
      scores[side].append(score)
  save(scores, 'scores/raw-'+test+'-'+feature)
  saveScores(scores, test, feature)
  sumScores(test, scores, positive, negative, features)

"""
  if feature=='duration':
    adjustment, adjusted=adjust(scores, positive, negative, feature)
    save({feature: adjustment}, 'scores/adjustments-'+test)
    save(adjusted, 'scores/adjusted-'+test)
    saveAdjusted(adjusted, test, feature)
  elif feature!='sequence':
    adjustments={}
    adjusteds={}
    for side in ['incoming', 'outgoing']:
      adjustment, adjusted=adjustSide(scores, positive, negative, feature, side)
      adjustments[side]=adjustment
      adjusteds[side]=adjusted
    save(adjustments, 'scores/adjustments-'+test+'-'+feature)
    save(adjusteds, 'scores/adjusted-'+test+'-'+feature)
#    saveAdjusted({adjusteds}, test, feature)
"""

def adjust(scores, positive, negative, feature):
  p=filter(lambda x: x!=0, map(lambda x: x[feature], scores[positive]))
  n=filter(lambda x: x!=0, map(lambda x: x[feature], scores[negative]))
  if numpy.mean(p)<0 and numpy.mean(n)<0:
    adjustment, p, n=adjustUpwards(p, n)
    return (adjustment, {positive: map(lambda x: {feature: x}, p), negative: map(lambda x: {feature: x}, n)})

def adjustSide(scores, positive, negative, feature, side):
  print('adjustSide')
  scores[positive]=filter(lambda x: feature in x[side], scores[positive])
  scores[negative]=filter(lambda x: feature in x[side], scores[negative])
  p=filter(lambda x: x!=0, map(lambda x: x[side][feature], scores[positive]))
  n=filter(lambda x: x!=0, map(lambda x: x[side][feature], scores[negative]))
  if (numpy.mean(p)<0 and numpy.mean(n)<0) or feature=='content':
    print('Adjusting upwards %f %f' % (numpy.mean(p), numpy.mean(n)))
    adjustment, p, n=adjustUpwards(p, n)
    return (adjustment, {positive: map(lambda x: {feature: x}, p), negative: map(lambda x: {feature: x}, n)})
  elif numpy.mean(p)>0 and numpy.mean(n)>0:
    print('Adjusting downwards %f %f' % (numpy.mean(p), numpy.mean(n)))
    adjustment, p, n=adjustDownwards(p, n)
    return (adjustment, {positive: map(lambda x: {feature: x}, p), negative: map(lambda x: {feature: x}, n)})
  else:
    print('No adjustment %f %f' % (numpy.mean(p), numpy.mean(n)))

def adjustUpwards(p, n):
  adjustment=0.001
  total=0
  while float(numWrong(p, True))/float(len(p)) > float(numWrong(n, False))/float(len(n)):
    print(numWrong(p, True), numWrong(n, False), total, numWrong(p, True)+numWrong(n, False))
    p=map(lambda x: x+adjustment, p)
    n=map(lambda x: x+adjustment, n)
    total=total+adjustment
  threshold=0.001
  totalThreshold=0
  return ({'offset': total, 'threshold': totalThreshold}, p, n)

def adjustDownwards(p, n):
  adjustment=0.01
  total=0
  print('Adjusting downwards loop %f %f %f %f' % (numpy.mean(p), numpy.mean(n), min(p), min(n)))
  print("Num wrong %f %f" % (float(numWrong(p, True))/float(len(p)), float(numWrong(n, False))/float(len(n))))
  pw=float(numWrong(p, True))/float(len(p))
  nw=float(numWrong(n, False))/float(len(n))
  while pw < nw:
    print(pw, nw, total)
    p=map(lambda x: x+adjustment, p)
    n=map(lambda x: x+adjustment, n)
    total=total-adjustment
    pw=float(numWrong(p, True))/float(len(p))
    nw=float(numWrong(n, False))/float(len(n))
  print("Ended loop")
  threshold=0.001
  totalThreshold=0
  return ({'offset': total, 'threshold': totalThreshold}, p, n)

def numWrong(items, direction):
  if direction:
    return len(filter(lambda x: x<0, items))
  else:
    return len(filter(lambda x: x>0, items))

def accuracy(p, n):
  ap=len(p)
  an=len(n)
  fp=numWrong(p, True)
  fn=numWrong(n, False)
  tp=ap-fp
  tn=an-fn
  up=0
  un=0
  s=(tp+tn)/(tp+tn+fp+fn)
  return s

def load(path):
  f=open(path)
  bs=f.read()
  f.close()
  return json.loads(bs)

def loadData(path):
  f=open(path)
  bs=f.read()
  f.close()
  return bs

def loadYaml(path):
  f=open(path)
  bs=f.read()
  f.close()
  return yaml.load(bs)

def merge(fits, fit, feature, directions):
  for protocol in fit:
    if not protocol in fits:
      fits[protocol]={}
    for item in fit[protocol]:
      for side in item:
        for connid in item[side]:
          if feature=='duration':
            if feature in item[side][connid]:
              value=item[side][connid][feature]
              if not connid in fits[protocol]:
                fits[protocol][connid]={}
              if not side in fits[protocol][connid]:
                fits[protocol][connid][side]={}
              fits[protocol][connid][side][feature]=value
          else:
            for direction in directions:
              if direction in item[side][connid] and feature in item[side][connid][direction]:
                value=item[side][connid][direction][feature]
                if not connid in fits[protocol]:
                  fits[protocol][connid]={}
                if not side in fits[protocol][connid]:
                  fits[protocol][connid][side]={}
                if not direction in fits[protocol][connid][side]:
                  fits[protocol][connid][side][direction]={}
                fits[protocol][connid][side][direction][feature]=value

testname=sys.argv[1]
#feature=sys.argv[2]
if not os.path.exists('scores'):
  os.mkdir('scores')
#tests=os.listdir('tests')
tests=[testname]
for test in tests:
#  fits=load('tests/'+test)
  fits={}
  features=loadYaml('adversaries/'+testname+'/'+'features')
  print(features)
  for feature in features:
    print(feature)
    fit=load('tests/'+testname+'-'+feature)
    merge(fits, fit, feature, features[feature])
#  print(fits)
  parts=test.split('-')
  positive=parts[0]
  negative=parts[1]
  saveFits(fits, test, features)
  scoreAdversary(test, fits, positive, negative, features)
