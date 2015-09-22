import os
import shutil
import sys

import math
import random
import logging

def choose(n):
  return int(random.random() * n)

if not os.path.exists('training'):
  os.mkdir('training')
if not os.path.exists('testing'):
  os.mkdir('testing')
for dataset in os.listdir('conns'):
  for protocol in os.listdir('conns/'+dataset):
    choices=[]
    for pcap in os.listdir('conns/'+dataset+'/'+protocol):
      for conn in os.listdir('conns/'+dataset+'/'+protocol+'/'+pcap):
        choices.append((pcap, conn))
    destination='training'
    while len(choices)>0:
      index=choose(len(choices))
      choice=choices.pop(index)
      if not os.path.exists('training/'+protocol):
        os.mkdir('training/'+protocol)
      if not os.path.exists('testing/'+protocol):
        os.mkdir('testing/'+protocol)
      shutil.copyfile('conns/'+dataset+'/'+protocol+'/'+choice[0]+'/'+choice[1], destination+'/'+protocol+'/'+choice[0]+'-'+choice[1])
      if destination=='training':
        destination='testing'
      else:
        destination='training'
