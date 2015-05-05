import json

def read(filename):
  f=open(filename)
  data=f.read()
  f.close()
  return json.loads(data)

m=read('scores/adjusted-HTTP-HTTPS-length')

f=open('length-adjusted.csv', 'w')
f.write("pi po ni no\n")
index=0
found=True
while found:
  found=False
  if index < len(m['incoming']['HTTP']):
    found=True
    f.write(str(m['incoming']['HTTP'][index]['length'])+" ")
  else:
    f.write("0 ")
  if index < len(m['outgoing']['HTTP']):
    found=True
    f.write(str(m['outgoing']['HTTP'][index]['length'])+" ")
  else:
    f.write("0 ")
  if index < len(m['incoming']['HTTPS']):
    found=True
    f.write(str(m['incoming']['HTTPS'][index]['length'])+" ")
  else:
    f.write("0 ")
  if index < len(m['outgoing']['HTTPS']):
    found=True
    f.write(str(m['outgoing']['HTTPS'][index]['length'])+" ")
  else:
    f.write("0 ")
  f.write("\n")
  index=index+1
f.close()
