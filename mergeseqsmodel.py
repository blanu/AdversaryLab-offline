import sys
import json

def parse(filename):
  f=open(filename)
  data=f.read()
  f.close()
  return json.loads(data)

def write(data, filename):
  f=open(filename, 'w')
  f.write(json.dumps(data))
  f.close()

model=parse('adversaries/'+sys.argv[1]+'/model')
parts=sys.argv[1].split('-')
p=parse('seqs/protocols/'+parts[0]+'-extracted')
n=parse('seqs/protocols/'+parts[1]+'-extracted')

model['positive']['incomingModel']['sequence']=p['incoming']
model['positive']['outgoingModel']['sequence']=p['outgoing']
model['negative']['incomingModel']['sequence']=n['incoming']
model['negative']['outgoingModel']['sequence']=n['outgoing']

write(model, 'adversaries/'+sys.argv[1]+'/model')
