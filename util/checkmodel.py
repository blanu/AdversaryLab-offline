import sys
import json

def parse(filename):
  f=open(filename)
  data=f.read()
  f.close()
  return json.loads(data)

model=parse('adversaries/'+sys.argv[1]+'/model')
print(model['negative']['incomingModel']['sequence'])
