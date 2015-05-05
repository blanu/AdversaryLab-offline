import json

def read(filename):
  f=open(filename)
  data=f.read()
  f.close()
  return json.loads(data)

m=read('adversaries/HTTP-HTTPS/model')
p=read('adversaries/HTTP-HTTPS/positive')
n=read('adversaries/HTTP-HTTPS/negative')

print(m['positive'].keys())
print(p['incomingStats'].keys())
print(n.keys())

f=open('length.csv', 'w')
f.write("mpi mpo mni mno pi po ni no\n")
for index in range(1440):
  values=[
    m['positive']['incomingModel']['length']['params'][index],
    m['positive']['outgoingModel']['length']['params'][index],
    m['negative']['incomingModel']['length']['params'][index],
    m['negative']['outgoingModel']['length']['params'][index],
    p['incomingStats']['lengths'][index],
    p['outgoingStats']['lengths'][index],
    n['incomingStats']['lengths'][index],
    n['outgoingStats']['lengths'][index]
  ]
  f.write(" ".join(map(str, values))+"\n")
f.close()

