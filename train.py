import os

import json
import logging
import numpy
import pystan
import pickle
import math
from md5 import md5

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

def fitDuration(lengths):
  lengths=filter(checkEntropy, lengths)
  if not lengths or len(lengths)<3:
    logging.error("Not enough samples for duration model")
    return None

  data={'samples': lengths, 'N': len(lengths)}
  fit=stan_cache('duration.stan', data=data, iter=1000, chains=4)
  logging.info(fit)
  samples=fit.extract(permuted=True)
  logging.info(samples)
  l=mean(samples['lambda'])
  logging.info(l)
  model=DurationModel(parameter=l)
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
  def __init__(self, parameter):
    self.parameter=parameter

  def serialize(self):
    return {'dist': 'exponential', 'params': [self.parameter]}    

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
  def __init__(self, positive, negative):
    self.positive=positive
    self.negative=negative

  def serialize(self):
    return {
      'positive': self.positive.serialize(),
      'negative': self.negative.serialize()
    }

  def save(self, path):
    write(self.serialize(), path)

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

def train(p, n):
  print('Training')
  pduration=fitDuration(p['duration'])
  pilength=fitLength(p['incomingStats']['lengths'])
  pientropy=fitEntropy(p['incomingStats']['entropy'])
  piflow=fitFlow(p['incomingStats']['flow'])
  picontent=fitContent(p['incomingStats']['content'])
  pimodel=StatsModel(length=pilength, entropy=pientropy, flow=piflow, content=picontent)
  polength=fitLength(p['outgoingStats']['lengths'])
  poentropy=fitEntropy(p['outgoingStats']['entropy'])
  poflow=fitFlow(p['outgoingStats']['flow'])
  pocontent=fitContent(p['outgoingStats']['content'])
  pomodel=StatsModel(length=polength, entropy=poentropy, flow=poflow, content=pocontent)
  pmodel=AdversaryProtocolModel(pduration, pimodel, pomodel)

  nduration=fitDuration(n['duration'])
  nilength=fitLength(n['incomingStats']['lengths'])
  nientropy=fitEntropy(n['incomingStats']['entropy'])
  niflow=fitFlow(n['incomingStats']['flow'])
  nicontent=fitContent(n['incomingStats']['content'])
  nimodel=StatsModel(length=pilength, entropy=pientropy, flow=piflow, content=picontent)
  nolength=fitLength(n['outgoingStats']['lengths'])
  noentropy=fitEntropy(n['outgoingStats']['entropy'])
  noflow=fitFlow(n['outgoingStats']['flow'])
  nocontent=fitContent(n['outgoingStats']['content'])
  nimodel=StatsModel(length=nilength, entropy=nientropy, flow=niflow, content=nicontent)
  nomodel=StatsModel(length=nolength, entropy=noentropy, flow=noflow, content=nocontent)
  nmodel=AdversaryProtocolModel(nduration, nimodel, nomodel)

  model=AdversaryModel(pmodel, nmodel)
  return model

ads=os.listdir('adversaries')
for ad in ads:
  p=load('adversaries/'+ad+'/positive')
  n=load('adversaries/'+ad+'/negative')
  result=train(p, n)
  result.save('adversaries/'+ad+'/model')
