import os
import sys

import json

datasets={}
protocols={}

def process(data):
  l=[]
  for b in data:
    l.append(ord(b))
  return l

def makeSequence(dataset, protocol, path):
  f=open(path+'/incoming')
  fi=process(f.read())
  f.close()

  f=open(path+'/outgoing')
  fo=process(f.read())
  f.close()

  if not dataset in datasets:
    datasets[dataset]={}
  if not protocol in datasets[dataset]:
    datasets[dataset][protocol]={'incoming': [], 'outgoing': []}
  datasets[dataset][protocol]['incoming'].append(fi)
  datasets[dataset][protocol]['outgoing'].append(fo)

  if not protocol in protocols:
    protocols[protocol]={'incoming': [], 'outgoing': []}
  protocols[protocol]['incoming'].append(fi)
  protocols[protocol]['outgoing'].append(fo)

def summarize(data):
  print('summarize')
  xmax=256
  ymax=1441
  results={}
  for side in ['incoming', 'outgoing']:
    summary=[]
    for offset in range(ymax):
      summary.append([0.0]*xmax)
    totals=[0.0]*ymax
    normal=[]
    for offset in range(ymax):
      normal.append([0.0]*xmax)
    for packet in data[side]:
      for offset in range(min(len(packet), ymax)):
        byte=packet[offset]
        summary[offset][byte]=summary[offset][byte]+1
        totals[offset]=totals[offset]+1
    for offset in range(len(summary)):
      if totals[offset]>0:
        for byte in range(len(summary[offset])):
          normal[offset][byte]=summary[offset][byte]/totals[offset]
    results[side]=normal
  return results

def saveSeq(data, path):
  f=open(path+'-raw', 'w')
  f.write(json.dumps(data))
  f.close()

  summary=summarize(data)

  f=open(path, 'w')
  f.write(json.dumps(summary))
  f.close()

  for side in ['incoming', 'outgoing']:
    f=open(path+'-'+side+'.csv', 'w')
    for y in range(len(summary[side])):
      f.write(' '.join(map(str, summary[side][y]))+"\n")
    f.close()

def saveSeqs():
  for dataset in datasets:
    if not os.path.exists('seqs/datasets/'+dataset):
      os.mkdir('seqs/datasets/'+dataset)
    for protocol in datasets[dataset]:
      data=datasets[dataset][protocol]
      saveSeq(data, 'seqs/datasets/'+dataset+'/'+protocol)

  for protocol in protocols:
    data=protocols[protocol]
    saveSeq(data, 'seqs/protocols/'+protocol)    

dataset=sys.argv[1]
if not os.path.exists('seqs'):
  os.mkdir('seqs')
if not os.path.exists('seqs/datasets'):
  os.mkdir('seqs/datasets')
if not os.path.exists('seqs/protocols'):
  os.mkdir('seqs/protocols')
for protocol in os.listdir('first/'+dataset):
  print(protocol)
  for pcap in os.listdir('first/'+dataset+'/'+protocol):
    print(pcap)
    for conn in os.listdir('first/'+dataset+'/'+protocol+'/'+pcap):
      path='first/'+dataset+'/'+protocol+'/'+pcap+'/'+conn
      if os.path.exists(path+'/incoming') and os.path.exists(path+'/outgoing'):
        makeSequence(dataset, protocol, path)
saveSeqs()
