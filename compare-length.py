import os
import sys

import json
import logging
import numpy
import pystan
import pickle
import math
from md5 import md5

from random import choice
import numpy
from numpy.random import normal, poisson, exponential, multinomial, gamma

def mean(l):
  return float(numpy.mean(l))

def stan_cache(model_name, **kwargs):
  f=open(model_name, 'rb')
  model_code=f.read()
  f.close()
  code_hash = md5(model_code.encode('ascii')).hexdigest()
  cache_fn = 'cached-{}-{}.pkl'.format(model_name, code_hash)
  try:
    sm = pickle.load(open(cache_fn, 'rb'))
  except:
    sm = pystan.StanModel(file=model_name)
    with open(cache_fn, 'wb') as f:
      pickle.dump(sm, f)
  else:
    logging.info("Using cached StanModel")
  return sm.sampling(**kwargs)

def compareCounts(countsA, countsB):
  e=0
  size=len(countsA)
  for x in range(size):
    a=countsA[x]
    b=countsB[x]
    e=e+rmse(a,b)
  return e

def checkFitNormalLengthModel(model, stats):
  sampleSize=1000
  bounds=[1,1440]
  countsA=generateNormalCounts(model, sampleSize, bounds)
  countsB=generateBootstrapCounts(stats, sampleSize, bounds)
  return compareCounts(countsA, countsB)

def checkFitMultinomialLengthModel(model, stats):
  sampleSize=1000
  bounds=[1,1440]
  countsA=generateMultinomialCounts(model, sampleSize, bounds)
  countsB=generateBootstrapCounts(stats, sampleSize, bounds)
  return compareCounts(countsA, countsB)

def generateBootstrapCounts(stats, sampleSize, bounds):
  size=(bounds[1]-bounds[0])+1
  counts=[0]*size
  samples=[]
  for x in range(sampleSize):
    samples.append(choice(stats))
  for sample in samples:
    if sample>bounds[0] and sample<bounds[1]:
      index=int(sample-bounds[0])
      counts[index]=counts[index]+1
  return counts

def generateExponentialSamples(model, sampleSize):
  print(model)
  beta=model['params'][0]
  return exponential(beta, sampleSize)

def generateGammaSamples(model, sampleSize):
  alpha=model['params'][0]
  beta=model['params'][1]
  return gamma(alpha, beta, sampleSize)

def generateNormalSamples(model, sampleSize):
  mean=model['params'][0]
  sd=model['params'][1]
  return normal(mean, sd, sampleSize)

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

def generateMultinomialCounts(model, sampleSize, bounds):
  dist=model['params']
  return list(multinomial(sampleSize, list(dist)))

def generateBootstrapSamples(stats, sampleSize):
  print(stats)
  samples=[]
  for x in range(sampleSize):
    samples.append(choice(stats))
  return samples

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

def fitLength(lengths):
  if not lengths:
    return None

  lengths=filter(lambda x: x<=1440, lengths)

  if len(lengths)<3:
    return None

  logging.info("fitting length with %d samples" % (len(lengths)))

  data={'samples': lengths, 'N': len(lengths)}
  fit=stan_cache('length.stan', data=data, iter=1000, chains=4)
  logging.info(fit)
  samples=fit.extract(permuted=True)
  logging.info(samples)
  theta1=mean(samples['theta'])
  sigma1=mean(samples['sigma'])
  logging.info((theta1, sigma1))
  logging.info('Length results:')
  logging.info(list((theta1, sigma1)))
  model=LengthModel(mean=theta1, sd=sigma1)
  logging.info(model)
  return model

def fitExponentialDuration(lengths):
  lengths=filter(checkEntropy, lengths)
  if not lengths or len(lengths)<3:
    logging.error("Not enough samples for duration model")
    return None

  data={'samples': lengths, 'N': len(lengths)}
  fit=stan_cache('duration-exponential.stan', data=data, iter=1000, chains=4)
  logging.info(fit)
  samples=fit.extract(permuted=True)
  logging.info(samples)
  l=mean(samples['lambda'])
  logging.info(l)
  model=DurationModel('exponential', [l])
  return model

def fitGammaDuration(lengths):
  lengths=filter(checkEntropy, lengths)
  if not lengths or len(lengths)<3:
    logging.error("Not enough samples for duration model")
    return None

  data={'samples': lengths, 'N': len(lengths)}
  fit=stan_cache('duration-gamma.stan', data=data, iter=1000, chains=4)
  logging.info(fit)
  samples=fit.extract(permuted=True)
  logging.info(samples)
  a=mean(samples['alpha'])
  b=mean(samples['beta'])
  model=DurationModel('gamma', [a, b])
  return model

def fitEntropy(samples):
  logging.info("Not enough samples for entropy model")
  if not samples or len(samples)<3:
    return None

  samples=filter(checkEntropy, samples)

  logging.info('Fitting entropy:')
  logging.info(samples)
  data={'samples': samples, 'N': len(samples)}
  fit=stan_cache('entropy.stan', data=data, iter=1000, chains=4)
  logging.info(fit)
  samples=fit.extract(permuted=True)
  logging.info(samples)
  theta1=mean(samples['theta'])
  sigma1=mean(samples['sigma'])
  logging.info((theta1, sigma1))
  logging.info(list((theta1, sigma1)))
  model=EntropyModel(mean=theta1, sd=sigma1)
  return model

def checkEntropy(sample):
  return sample>0

def fitFlow(samples):
  if not samples or len(samples)<3:
    return None

  data={'samples': samples, 'N': len(samples)}
  fit=stan_cache('flow.stan', data=data, iter=1000, chains=4)
  logging.info(fit)
  samples=fit.extract(permuted=True)
  logging.info(samples)
  l=mean(samples['lambda'])
  logging.info(l)
  model=FlowModel(parameter=l)
  return model

def fitContent(counts):
  if not counts or len(counts)!=256:
    return None

  logging.info('Fitting content model:')
  logging.info(counts)
  data={'counts': counts}
  fit=stan_cache('content.stan', data=data, iter=1000, chains=2)
  logging.info('Loaded model')
  samples=fit.extract(permuted=True)
  thetas=samples['theta']
  theta=map(float, list(thetas[0])) # FIXME - This is a bad way to generate a summary statistic for theta
  logging.info(theta)
  model=ContentModel(distribution=theta)
  return model

class DurationModel:
  def __init__(self, dist, params):
    self.dist=dist
    self.params=params

  def serialize(self):
    return {'dist': self.dist, 'params': self.params}

class FlowModel:
  def __init__(self, parameter):
    self.parameter=parameter

  def serialize(self):
    return {'dist': 'poisson', 'params': [self.parameter]}

class EntropyModel:
  def __init__(self, mean, sd):
    self.mean=mean
    self.sd=sd

  def serialize(self):
    return {'dist': 'normal', 'params': [self.mean, self.sd]}

class LengthModel:
  def __init__(self, mean, sd):
    self.mean=mean
    self.sd=sd

  def serialize(self):
    return {'dist': 'normal', 'params': [self.mean, self.sd]}

class ContentModel:
  def __init__(self, distribution):
    self.distribution=distribution

  def serialize(self):
    return {'dist': 'multinomial', 'params': self.distribution}

class StatsModel:
  def __init__(self, length, entropy, flow, content):
    self.length=length
    self.entropy=entropy
    self.flow=flow
    self.content=content

  def serialize(self):
    return {
      'length': self.length.serialize(),
      'entropy': self.entropy.serialize(),
      'flow': self.flow.serialize(),
      'content': self.content.serialize()
    }

class AdversaryProtocolModel:
  def __init__(self, duration, incomingModel, outgoingModel):
    self.duration=duration
    self.incomingModel=incomingModel
    self.outgoingModel=outgoingModel

  def serialize(self):
    return {
      'duration': self.duration.serialize(),
      'incomingModel': self.incomingModel.serialize(),
      'outgoingModel': self.outgoingModel.serialize()
    }

class AdversaryModel:
  def __init__(self, dist, positive, negative):
    self.dist=dist
    self.positive=positive
    self.negative=negative

  def serialize(self):
    return {
      'positive': self.positive.serialize(),
      'negative': self.negative.serialize()
    }

  def save(self, path):
    write(self.serialize(), path+'/'+self.dist)

def load(path):
  f=open(path)
  bs=f.read()
  f.close()
  return json.loads(bs)

def write(model, path):
  bs=json.dumps(model)
  f=open(path, 'w')
  f.write(bs)
  f.close()

def writeCSV(model, path):
  bs=json.dumps(model)
  f=open(path, 'w')
  for key in model:
    values=model[key]
    f.write(key+' '+str(values['positive'])+' '+str(values['negative'])+' '+str(values['total'])+"\n")
  f.close()

def clean(data):
  filtered=filter(lambda x: x>0, data)
  s=sorted(filtered)
  l=len(s)
  offset=int(l*0.025)
  cleaned=s[offset:-offset]
  return cleaned

def compare(ni, no, mi, mo, p, n):
  print('Training')
  nip=checkFitNormalLengthModel(ni['positive'], p['duration'])
  nop=checkFitNormalLengthModel(no['positive'], p['duration'])
  mip=checkFitMultinomialLengthModel(mi['positive'], p['duration'])
  mop=checkFitMultinomialLengthModel(mi['positive'], p['duration'])

  nin=checkFitNormalLengthModel(ni['positive'], n['duration'])
  non=checkFitNormalLengthModel(no['positive'], n['duration'])
  min=checkFitMultinomialLengthModel(mi['positive'], n['duration'])
  mon=checkFitMultinomialLengthModel(mo['positive'], n['duration'])

  return {
    'normal-incoming': {'positive': nip, 'negative': nin, 'total': nip+nin},
    'normal-outgoing': {'positive': nop, 'negative': non, 'total': nop+non},
    'multinomial-incoming': {'positive': mip, 'negative': min, 'total': mip+min},
    'multinomial-outgoing': {'positive': mop, 'negative': mon, 'total': mop+mon}
  }

ad=sys.argv[1]
if not os.path.exists('rmse'):
  os.mkdir('rmse')
if not os.path.exists('rmse/'+ad):
  os.mkdir('rmse/'+ad)
ni=load('compare/'+ad+'/length-incoming/normal')
no=load('compare/'+ad+'/length-outgoing/normal')
mi=load('compare/'+ad+'/length-incoming/multinomial')
mo=load('compare/'+ad+'/length-outgoing/multinomial')
p=load('adversaries/'+ad+'/positive')
n=load('adversaries/'+ad+'/negative')
result=compare(ni, no, mi, mo, p, n)
write(result, 'rmse/'+ad+'/length')
writeCSV(result, 'rmse/'+ad+'/length.csv')
