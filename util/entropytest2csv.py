import json

f=open('tests/HTTP-HTTPS')
data=f.read()
f.close()

data=json.loads(data)

for prot in ['HTTP', 'HTTPS']:
  f=open('tests/'+prot+'-entropy.csv', 'w')
  f.write("pi po ni no\n")
  for item in data[prot]:
    pi=item['positive']['incoming']['entropy']
    po=item['positive']['outgoing']['entropy']
    ni=item['negative']['incoming']['entropy']
    no=item['negative']['outgoing']['entropy']

    print(pi, po, ni, no)
    vals=[pi, po, ni, no]
    s=" ".join(map(str, vals))
    f.write(s)
    f.write("\n")
  f.close()
