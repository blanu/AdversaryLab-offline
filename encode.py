import os

import json
import logging
import subprocess

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

def makeEncoding(encoding, positive):
  ihuffman=makeHuffman(positive[u'incomingStats'][u'content'])
  ohuffman=makeHuffman(positive[u'outgoingStats'][u'content'])
  encoding[u'incomingModel'][u'huffman']=ihuffman
  encoding[u'outgoingModel'][u'huffman']=ohuffman
  return encoding

def parse(item):
  if item=='':
    return None
  a=[]
  for x in item:
    if x=="0":
      a.append(False)
    elif x=="1":
      a.append(True)
  return a

def makeHuffman(dist):
  f=open('temp.csv', 'w')
  for x in dist:
    f.write(str(x))
    f.write("\n")
  f.close()
  subprocess.call(['../Dust-tools/dist/build/huffman/huffman', 'temp.csv', 'huffman.export'])

  f=open('huffman.export')
  s=f.read()
  f.close()

  l=s.split("\n")
  l=map(parse, l)
  l=filter(lambda x: x!=None, l)

  return l

if not os.path.exists('encodings'):
  os.mkdir('encodings')
ads=os.listdir('adversaries')
for ad in ads:
  if not os.path.exists('encodings/'+ad):
    os.mkdir('encodings/'+ad)
  model=load('adversaries/'+ad+'/model')
  positive=load('adversaries/'+ad+'/positive')
  negative=load('adversaries/'+ad+'/negative')

  encoding=makeEncoding(model['positive'], positive)
  write(encoding, 'encodings/'+ad+'/positive')

  encoding=makeEncoding(model['negative'], negative)
  write(encoding, 'encodings/'+ad+'/negative')
