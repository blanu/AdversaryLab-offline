import os
import sys

import json
import math

from scipy.stats import norm
import matplotlib.pyplot as plt
from bisect import bisect_left

def load(path):
  f=open(path)
  bs=f.read()
  f.close()
  return json.loads(bs)

class discrete_cdf:
    def __init__(self, data):
        self._data = data # must be sorted
        self._data_len = float(len(data))

    def __call__(self, point):
        return (len(self._data[:bisect_left(self._data, point)]) /
                self._data_len)

def savePlot(xvalues, yvalues, filename):
  plt.clf()
  plt.plot(xvalues, yvalues)
  plt.savefig(filename)

def saveCSV(xvalues, yvalues, filename):
  f=open(filename, 'w')
  for index in range(len(xvalues)):
    f.write(str(xvalues[index])+" "+str(yvalues[index])+"\n")
  f.close()

def plotData(data, filename):
  xvalues=range(len(data))
  saveCSV(xvalues, data, filename+'.csv')
  savePlot(xvalues, data, filename+'.png')

def plotSorted(data, filename):
  data = sorted(data)
  xvalues=range(len(data))
  saveCSV(xvalues, data, filename+'.csv')
  savePlot(xvalues, data, filename+'.png')

def plotCDF(data, filename):
  data = sorted(data)
  cdf = discrete_cdf(data)
  xvalues=range(0, int(math.ceil(max(data))))
  saveCSV(xvalues, [cdf(point) for point in xvalues], filename+'.csv')
  savePlot(xvalues, [cdf(point) for point in xvalues], filename+'.png')

def plotFeature(dataset, protocol, name, data):
  plotData(data, 'graphs/'+dataset+'/'+protocol+'/'+name+'_data')
  plotSorted(data, 'graphs/'+dataset+'/'+protocol+'/'+name+'_sorted')
  plotCDF(data, 'graphs/'+dataset+'/'+protocol+'/'+name+'_cdf')

protocolData={}
if not os.path.exists('summaries'):
  os.mkdir('summaries')
datasets=os.listdir('datasets')
for dataset in datasets:
  protocols=os.listdir('datasets/'+dataset)
  for protocol in protocols:
    if not protocol in protocolData:
      protocolData[protocol]={}

    if not os.path.exists('summaries/'+protocol):
      os.mkdir('summaries/'+protocol)
    if not os.path.exists('summaries/'+protocol+'/duration'):
      os.mkdir('summaries/'+protocol+'/duration')

    model=load('datasets/'+dataset+'/'+protocol)
    plotFeature(dataset, protocol, 'duration', model['duration'])
    plotFeature(dataset, protocol, 'incoming_length', model['incomingStats']['lengths'])
    plotFeature(dataset, protocol, 'outgoing_length', model['outgoingStats']['lengths'])
    plotFeature(dataset, protocol, 'incoming_flow', model['incomingStats']['flow'])
    plotFeature(dataset, protocol, 'outgoing_flow', model['outgoingStats']['flow'])
    plotFeature(dataset, protocol, 'incoming_entropy', model['incomingStats']['entropy'])
    plotFeature(dataset, protocol, 'outgoing_entropy', model['outgoingStats']['entropy'])
    plotFeature(dataset, protocol, 'incoming_content', model['incomingStats']['content'])
    plotFeature(dataset, protocol, 'outgoing_content', model['outgoingStats']['content'])
