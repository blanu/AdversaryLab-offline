import json

f=open('tests/HTTP-HTTPS-sequence')
data=f.read()
f.close()

data=json.loads(data)

for prot in ['HTTP', 'HTTPS']:
  f=open('tests/'+prot+'-sequence.csv', 'w')
  f.write("pi po ni no\n")
  for item in data[prot]:
    try:
      pi=item['positive']['incoming']['sequence']
      po=item['positive']['outgoing']['sequence']
      ni=item['negative']['incoming']['sequence']
      no=item['negative']['outgoing']['sequence']
    except:
      continue

    print(pi, po, ni, no)
    vals=[pi, po, ni, no]
    s=" ".join(map(str, vals))
    f.write(s)
    f.write("\n")
  f.close()
