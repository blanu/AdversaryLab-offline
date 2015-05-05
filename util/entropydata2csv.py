import json

f=open('adversaries/HTTP-HTTPS/positive')
data=f.read()
f.close()
p=json.loads(data)

f=open('adversaries/HTTP-HTTPS/negative')
data=f.read()
f.close()
n=json.loads(data)

pi=p['incomingStats']['entropy']
po=p['outgoingStats']['entropy']
ni=n['incomingStats']['entropy']
no=n['outgoingStats']['entropy']

maxindex=min(len(pi), len(po), len(ni), len(no))
print(maxindex)

f=open('entropy-data.csv', 'w')
f.write("pi po ni no\n")
for index in range(maxindex):
  print(pi[index], po[index], ni[index], no[index])
  vals=[pi[index], po[index], ni[index], no[index]]
  s=" ".join(map(str, vals))
  f.write(s)
  f.write("\n")
f.close()
