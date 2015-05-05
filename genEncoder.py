import sys
import json

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

ad=sys.argv[1]
out=sys.argv[2]
parts=ad.split('-')
positive=parts[0]
negative=parts[1]

model=load('adversaries/'+ad+'/model')

write(model['positive'], out+'/'+positive+'.json')
write(model['negative'], out+'/'+negative+'.json')
