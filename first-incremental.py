import sys
import os
import shutil

import math
import json
import logging

from scapy.all import sniff, IPv6, IP, UDP, TCP, rdpcap, wrpcap

portTable={
  'HTTP': 80,
  'HTTPS': 443,
  'HTTPRSS': 80,
  'WebRTC': 57162,
  'uProxy': 56963,
  'DustRTSP': 36747
}

class PcapStatInfo:
  def __init__(self):
    self.duration=[]
    self.isizes=[0]*1500
    self.icontent=[0]*256
    self.ientropy=[]
    self.iflow=[]
    self.osizes=[0]*1500
    self.ocontent=[0]*256
    self.oentropy=[]
    self.oflow=[]

class Connection():
  def __init__(self, parent, pcap, portsId, duration, incomingStats, outgoingStats):
    self.parent=parent
    self.pcap=pcap
    self.portsId=portsId
    self.duration=duration
    self.incomingStats=incomingStats
    self.outgoingStats=outgoingStats

  def save(self, path):
    path=path+'/'+self.portsId
    print('Saving to '+path)
    data=self.serialize()
    s=json.dumps(data)
    f=open(path, 'w')
    f.write(s)
    f.close()

  def serialize(self):
    return {
      'duration': self.duration,
      'incomingStats': self.incomingStats.serialize(),
      'outgoingStats': self.outgoingStats.serialize()
    }

class DatasetProtocolStats():
  def __init__(self, dataset, protocol, duration, incomingStats, outgoingStats):
    self.dataset=dataset
    self.protocol=protocol
    self.duration=duration
    self.incomingStats=incomingStats
    self.outgoingStats=outgoingStats

  def save(self, path):
    path=path+'/'+self.dataset+'/'+self.protocol
    print('Saving to '+path)
    data=self.serialize()
    s=json.dumps(data)
    f=open(path, 'w')
    f.write(s)
    f.close()

  def serialize(self):
    return {
      'duration': self.duration,
      'incomingStats': self.incomingStats.serialize(),
      'outgoingStats': self.outgoingStats.serialize()
    }

class ProtocolStats():
  def __init__(self, protocol, duration, incomingStats, outgoingStats):
    self.protocol=protocol
    self.duration=duration
    self.incomingStats=incomingStats
    self.outgoingStats=outgoingStats

  def save(self, path):
    path=path+'/'+self.protocol
    print('Saving to '+path)
    data=self.serialize()
    s=json.dumps(data)
    f=open(path, 'w')
    f.write(s)
    f.close()

  def serialize(self):
    return {
      'duration': self.duration,
      'incomingStats': self.incomingStats.serialize(),
      'outgoingStats': self.outgoingStats.serialize()
    }

class Stats():
  def __init__(self, parent, lengths, content, entropy, flow):
    self.parent=parent
    self.lengths=lengths
    self.content=content
    self.entropy=entropy
    self.flow=flow

  def serialize(self):
    return {
      'lengths': self.lengths,
      'content': self.content,
      'entropy': self.entropy,
      'flow': self.flow
    }

class DirectionalSummaryStats():
  def __init__(self, lengths, content, entropy, flow):
    self.lengths=lengths
    self.content=content
    self.entropy=entropy
    self.flow=flow

  def serialize(self):
    return {
      'lengths': self.lengths,
      'content': self.content,
      'entropy': self.entropy,
      'flow': self.flow
    }

def calculateEntropy(contents):
  total=sum(contents)

  u=0
  for count in contents:
    if total==0:
      p=0
    else:
      p=float(count)/float(total)
    if p==0:
      e=0
    else:
      e=-p*math.log(p, 2)
    u=u+e
  return float(u)

def streamId(packet):
  if 'IP' in packet:
    ip=packet['IP']
    src=ip.fields['src']
    dst=ip.fields['dst']
  elif 'IPv6' in packet:
    ip=packet['IPv6']
    src='['+ip.fields['src']+']'
    dst='['+ip.fields['dst']+']'
  else:
    logging.error('Non-IP packet: '+str(packet.summary()))
    return None

  if 'UDP' in packet:
    ut='udp'
    dport=packet['UDP'].fields['dport']
    sport=packet['UDP'].fields['sport']
  elif 'TCP' in packet:
    ut='tcp'
    dport=packet['TCP'].fields['dport']
    sport=packet['TCP'].fields['sport']
  else:
    logging.error('Packet not UDP or TCP: '+str(packet.summary()))
    return None

  id=ut+'_'+src+'_'+str(sport)+'_'+dst+'_'+str(dport)
  return id

def getPorts(packet):
  if 'IP' in packet or 'IPv6' in packet:
    if 'UDP' in packet:
      dport=packet['UDP'].fields['dport']
      sport=packet['UDP'].fields['sport']
      return (dport, sport)
    elif 'TCP' in packet:
      dport=packet['TCP'].fields['dport']
      sport=packet['TCP'].fields['sport']
      return (dport, sport)
  return None

def getSortedPorts(packet):
  if 'IP' in packet or 'IPv6' in packet:
    if 'UDP' in packet:
      dport=packet['UDP'].fields['dport']
      sport=packet['UDP'].fields['sport']
      if sport<dport:
        return (sport, dport)
      else:
        return (dport, sport)
    elif 'TCP' in packet:
      dport=packet['TCP'].fields['dport']
      sport=packet['TCP'].fields['sport']
      if sport<dport:
        return (sport, dport)
      else:
        return (dport, sport)
  return None

# generator
def getTimestamps(packets):
  for packet in packets:
    yield int(packet.time)

# generator
def absoluteToRelative(base, timestamps):
  for timestamp in timestamps:
    yield timestamp-base

# generator
def packetsPerSecond(offsets):
  current=0
  count=0
  for offset in offsets:
    if offset==current:
      count=count+1
    else:
      yield count
      for step in range(offset-(current+1)):
        yield 0
      count=1
    current=offset

def calculateFlow(packets):
  if packets and len(packets)>0:
    base=int(packets[0].time)
    return packetsPerSecond(absoluteToRelative(base, getTimestamps(packets)))
  else:
    return []

def calculateDuration(timestamps):
  if len(timestamps)<2:
    return 0
  else:
    l=sorted(timestamps)
    first=timestamps[0]
    last=timestamps[-1]
    duration=last-first
    if duration<0:
      print('Error! Negative duration! %d' % (duration))
      return 0
    else:
      return duration

class StreamStatInfo:
  def __init__(self):
    self.sizes=[0]*1500
    self.content=[0]*256
    self.timestamps=[]
    self.flow=[]
    self.entropy=0
    self.duration=0

class PcapStatInfo:
  def __init__(self):
    self.duration=[]
    self.isizes=[0]*1500
    self.icontent=[0]*256
    self.ientropy=[]
    self.iflow=[]
    self.osizes=[0]*1500
    self.ocontent=[0]*256
    self.oentropy=[]
    self.oflow=[]

def getFirstPacketContents(packet):
  bs=bytes(packet.load)
  l=[0]*len(bs)
  for x in range(len(bs)):
    l[x]=ord(bs[x])
  return l

class FirstPair:
  def __init__(self):
    self.firstIn=None
    self.firstOut=None

  def setIn(self, p):
    if self.firstIn==None:
      if p.load!=None:
        self.firstIn=p

  def setOut(self, p):
    if self.firstOut==None:
      if p.load!=None:
        self.firstOut=p

class CaptureStats:
  def __init__(self, pcap, port):
    self.pcap=pcap
    self.port=port
    self.data={}
    self.streams={}
    self.firsts={}

  def processPcap(self, streamfile):
    self.splitStreams(streamfile)
    print("Processing %d streams" % (len(self.streams.keys())))
    for key in self.data:
      pair=self.data[key]

      for index, packet in [(0, pair.firstIn), (1, pair.firstOut)]:
       if packet!=None:
         self.processPacket(key, index, packet)

    return self.combineStreams()

  def splitStreams(self, tracefile):
    print('Split streams')
    try:
      packets=rdpcap(tracefile)
    except:
      logging.error('Error reading pcap file '+tracefile)
      return
    print("Processing %d packets" % (len(list(packets))))
    for packet in packets:
      if ('IP' in packet or 'IPv6' in packet) and ('TCP' in packet or 'UDP' in packet) and 'Raw' in packet and len(packet.load)>0:
        ports=getPorts(packet)
        if self.port==ports[0]:
          portIndex=0
        elif self.port==ports[1]:
          portIndex=1
        else:
          #print('Unknown ports %d/%d' % (ports[0], ports[1]))
          continue
        sports=getSortedPorts(packet)
        if ports:
          skey=str(sports[0])+":"+str(sports[1])
          if not (skey in self.streams):
            self.streams[skey]=[[], []]
          self.streams[skey][portIndex].append(packet)
          if not skey in self.data:
            self.data[skey]=FirstPair()
          if portIndex==0: # Incoming
            self.data[skey].setIn(packet)
          else:            # Outgoing
            self.data[skey].setOut(packet)
          if not skey in self.firsts:
            self.firsts[skey]=[None, None]

  def processPacket(self, stream, portIndex, packet):
    contents=bytes(packet.load)
    self.firsts[stream][portIndex]=contents

  def combineStreams(self):
    print('Combine streams')
    result={}
    for key in self.firsts:
      value=self.firsts[key]
      if value[0]!=None and value[1]!=None:
        result[key]=value
    return result

def saveFirst(data, filename):
  f=open(filename, 'w')
  f.write(data)
  f.close()

def makeFirst(dataset, protocol, pcap, port):
  print('Processing '+dataset+' '+protocol+' '+pcap)
  stats=CaptureStats(pcap, port)
  conns=stats.processPcap('pcaps/'+dataset+'/'+protocol+'/'+pcap)
  print("Found %d conns" % (len(conns)))
  for key in conns:
    conn=conns[key]
    if not os.path.exists('first/'+dataset+'/'+protocol+'/'+pcap+'/'+key):
      os.mkdir('first/'+dataset+'/'+protocol+'/'+pcap+'/'+key)
    saveFirst(conn[0], 'first/'+dataset+'/'+protocol+'/'+pcap+'/'+key+'/incoming')
    saveFirst(conn[1], 'first/'+dataset+'/'+protocol+'/'+pcap+'/'+key+'/outgoing')
  return conns

dataset=sys.argv[1]
protocol=sys.argv[2]
pcap=sys.argv[3]
port=int(sys.argv[4])
if not os.path.exists('first'):
  os.mkdir('first')
protocolDataMap={}
if not os.path.exists('first/'+dataset):
  os.mkdir('first/'+dataset)
if not os.path.exists('datasets/'+dataset):
  os.mkdir('datasets/'+dataset)
if not os.path.exists('first/'+dataset+'/'+protocol):
  os.mkdir('first/'+dataset+'/'+protocol)
conns=[]
if pcap!='all':
  pcaps=[pcap]
else:
  pcaps=os.listdir('pcaps/'+dataset+'/'+protocol)
  print(pcaps)
  for pcap in pcaps:
    print('Processing pcap '+pcap)
    if not os.path.exists('first/'+dataset+'/'+protocol+'/'+pcap):
      os.mkdir('first/'+dataset+'/'+protocol+'/'+pcap)
    makeFirst(dataset, protocol, pcap, port)
