import json

f=open('adversaries/HTTP-HTTPS/model')
data=f.read()
f.close()

data=json.loads(data)

pi=data['positive']['incomingModel']['content']['params']
po=data['positive']['outgoingModel']['content']['params']
ni=data['negative']['incomingModel']['content']['params']
no=data['negative']['outgoingModel']['content']['params']

f=open('content.csv', 'w')
f.write("pi po ni no\n")
for index in range(256):
    vals=[pi[index], po[index], ni[index], no[index]]
    s=" ".join(map(str, vals))
    f.write(s)
    f.write("\n")
f.close()
