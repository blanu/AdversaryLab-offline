import os
import sys
import shutil

import math
import logging

from scapy.all import sniff, IPv6, IP, UDP, TCP, rdpcap, wrpcap

class Connection():
  def __init__(self, parent, pcap, portsId, duration, incomingStats, outgoingStats):
    self.parent=parent
    self.pcap=pcap
    self.portsId=portsId
    self.duration=duration
    self.incomingStats=incomingStats
    self.outgoingStats=outgoingStats

  def save(self, path):
    print('Saving to '+path)

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
      return (sport, dport)
    elif 'TCP' in packet:
      dport=packet['TCP'].fields['dport']
      sport=packet['TCP'].fields['sport']
      return (sport, dport)
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
    return last-first

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

class CaptureStats:
  def __init__(self, pcap, port):
    self.pcap=pcap
    self.port=port
    self.data={}
    self.streams={}

  def processPcap(self, streamfile):
    self.splitStreams(streamfile)
    for key in self.streams:
      packets=self.streams[key]
      infos=self.data[key]
      infos[0].flow=calculateFlow(packets[0])
      infos[1].flow=calculateFlow(packets[1])

      for index in [0,1]:
        side=packets[index]
        for packet in side:
          self.processPacket(key, index, packet)

      return self.combineStreams()

  def splitStreams(self, tracefile):
    try:
      packets=rdpcap(tracefile)
    except:
      logging.error('Error reading pcap file '+tracefile)
      return
    for packet in packets:
      if ('IP' in packet or 'IPv6' in packet) and ('TCP' in packet or 'UDP' in packet) and 'Raw' in packet and len(packet.load)>0:
        ports=getPorts(packet)
        if self.port==ports[0]:
          portIndex=0
        elif self.port==ports[1]:
          portIndex=1
        else:
          #logging.error('Unknown port')
          continue
        sports=getSortedPorts(packet)
        if ports:
          skey=str(sports[0])+":"+str(sports[1])
          if not (skey in self.streams):
            self.streams[skey]=[[], []]
          self.streams[skey][portIndex].append(packet)
          if not skey in self.data:
            self.data[skey]=[StreamStatInfo(), StreamStatInfo()]

  def getFirstPacketContents(self, packet):
    bs=bytes(packet.load)
    l=[0]*len(bs)
    for x in range(len(bs)):
      l[x]=ord(bs[x])
    return l

  def processPacket(self, stream, portIndex, packet):
    info=self.data[stream][portIndex]
    sz=info.sizes

    contents=bytes(packet.load)
    length=len(contents)

    if length>0 and length<1500:
      sz[length]=sz[length]+1
    else:
      logging.error('Bad length: '+str(length))

    for c in contents:
      x=ord(c)
      info.content[x]=info.content[x]+1

    info.timestamps.append(float(packet.time))

    info.sizes=sz
    self.data[stream][portIndex]=info

  def combineStreams(self):
    conns=[]
    pstats=PcapStatInfo()
    for key in self.data:
      info=self.data[key]
      info[0].entropy=calculateEntropy(info[0].content)
      info[1].entropy=calculateEntropy(info[1].content)
      info[0].duration=calculateDuration(info[0].timestamps+info[1].timestamps)
      info[1].duration=info[0].duration
      istats=Stats(parent=self.pcap, lengths=info[0].sizes, content=info[0].content, entropy=info[0].entropy, flow=list(info[0].flow))
      ostats=Stats(parent=self.pcap, lengths=info[1].sizes, content=info[1].content, entropy=info[1].entropy, flow=list(info[1].flow))
      conn=Connection(parent=self.pcap, pcap=self.pcap, portsId=key, duration=float(info[0].duration), incomingStats=istats, outgoingStats=ostats)
      conns.append(conn)

      pstats.duration.append(info[0].duration)

      pstats.isizes=pstats.isizes+info[0].sizes
      pstats.icontent=pstats.icontent+info[0].content
      pstats.ientropy.append(info[0].entropy)
      pstats.iflow=pstats.iflow+info[0].flow

      pstats.osizes=pstats.osizes+info[1].sizes
      pstats.ocontent=pstats.ocontent+info[1].content
      pstats.oentropy.append(info[1].entropy)
      pstats.oflow=pstats.oflow+info[1].flow

#    pistats=DirectionalSummaryStats(parent=pcap, lengths=pstats.isizes, content=pstats.icontent, entropy=pstats.ientropy, flow=pstats.iflow)
#    postats=DirectionalSummaryStats(parent=pcap, lengths=pstats.osizes, content=pstats.ocontent, entropy=pstats.oentropy, flow=pstats.oflow)
#    pcapStats=PcapStats(parent=pcap, pcap=pcap, duration=pstats.duration, incomingStats=pistats, outgoingStats=postats)

    return conns

def makeConns(dataset, protocol, pcap):
  stats=CaptureStats(port)
  conns=stats.processPcap(pcap)
  for conn in conns:
    conn.save('conns/'+dataset+'/'+protocol+'/'+pcap)

port=int(sys.argv[1])
datasets=os.listdir('pcaps')
for dataset in datasets:
  if not os.path.exists('conns/'+dataset):
    os.mkdir('conns/'+dataset)
  protocols=os.listdir('protocols')
  for protocol in protocols:
    if not os.path.exists('conns/'+dataset+'/'+protocol):
      os.mkdir('conns/'+dataset+'/'+protocol)
    pcaps=os.listdir('conns/'+dataset+'/'+protocol)
    for pcap in pcaps:
      if not os.path.exists('conns/'+dataset+'/'+protocol+'/'+pcap):
        os.mkdir('conns/'+dataset+'/'+protocol+'/'+pcap)
      makeConns(dataset, protocol, pcap, port)
