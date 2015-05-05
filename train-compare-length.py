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

class ContentModel:
  def __init__(self, distribution):
    self.distribution=distribution

  def serialize(self):
    return {'dist': 'multinomial', 'params': self.distribution}

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

def checkFitExponentialDurationModel(model, stats):
  sampleSize=1000
  samplesA=generateExponentialSamples(model, sampleSize)
  samplesB=generateBootstrapSamples(stats, sampleSize)
  return compareSamples(samplesA, samplesB)

def checkFitGammaDurationModel(model, stats):
  sampleSize=1000
  samplesA=generateGammaSamples(model, sampleSize)
  samplesB=generateBootstrapSamples(stats, sampleSize)
  return compareSamples(samplesA, samplesB)

def generateExponentialSamples(model, sampleSize):
  beta=model['params'][0]
  return exponential(beta, sampleSize)

def generateGammaSamples(model, sampleSize):
  alpha=model['params'][0]
  beta=model['params'][1]
  return gamma(alpha, beta, sampleSize)

def generateBootstrapSamples(stats, sampleSize):
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

def fitNormalLength(lengths):
  if not lengths:
    return None

  lengths=filter(lambda x: x<=1440, lengths)

  if len(lengths)<3:
    return None

  logging.info("fitting length with %d samples" % (len(lengths)))

  data={'samples': lengths, 'N': len(lengths)}
  fit=stan_cache('length-normal.stan', data=data, iter=1000, chains=4)
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

def fitMultinomialLength(lengths):
  if not lengths or len(lengths)<1440:
    print('Bad lengths: %d' % (len(lengths)))
    return None
  if len(lengths)>1440:
    lengths=lengths[:1440]

  logging.info("fitting length with %d samples" % (len(lengths)))

  counts=lengths

  logging.info('Fitting multinomial length model:')
  logging.info(counts)
  data={'counts': counts}
  fit=stan_cache('length-multinomial.stan', data=data, iter=1000, chains=2)
  logging.info('Loaded model')
  samples=fit.extract(permuted=True)
  thetas=samples['theta']
  theta=map(float, thetas[0])
  logging.info(theta)
  model=LengthModel(distribution=theta)

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
  theta=float(numpy.mean(thetas[0]))
  logging.info(theta)
  model=ContentModel(distribution=theta)
  return model

class LengthModel:
  def __init__(self, mean, sd):
    self.mean=mean
    self.sd=sd

  def serialize(self):
    return {'dist': 'normal', 'params': [self.mean, self.sd]}

class AdversaryProtocolModel:
  def __init__(self, length, incomingModel, outgoingModel):
    self.length=length
    self.incomingModel=incomingModel
    self.outgoingModel=outgoingModel

  def serialize(self):
    return {
      'length': self.length.serialize(),
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

def train(p, n, direction):
  print('Training')
  print(p[direction+'Stats'].keys())
  nplength=fitNormalLength(p[direction+'Stats']['lengths'])
  nnlength=fitNormalLength(n[direction+'Stats']['lengths'])

  mplength=fitMultinomialLength(p[direction+'Stats']['lengths'])
  mnlength=fitMultinomialLength(n[direction+'Stats']['lengths'])

  nmodel=AdversaryModel('normal', nplength, nnlength)
  mmodel=AdversaryModel('multinomial', mplength, mnlength)
  return [nmodel, mmodel]

ad=sys.argv[1]
if not os.path.exists('compare'):
  os.mkdir('compare')
if not os.path.exists('compare/'+ad):
  os.mkdir('compare/'+ad)
if not os.path.exists('compare/'+ad+'/length'):
  os.mkdir('compare/'+ad+'/length')
p=load('adversaries/'+ad+'/positive')
n=load('adversaries/'+ad+'/negative')
print(p.keys())
for direction in ['incoming', 'outgoing']:
  results=train(p, n, direction)
  for result in results:
    if not os.path.exists('compare/'+ad+'/length-'+direction):
      os.mkdir('compare/'+ad+'/length-'+direction)
    result.save('compare/'+ad+'/length-'+direction)
