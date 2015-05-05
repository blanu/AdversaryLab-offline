import json

f=open('adversaries/HTTP-HTTPS/model')
data=f.read()
f.close()

data=json.loads(data)

pi=data['positive']['incomingModel']['entropy']['params']
po=data['positive']['outgoingModel']['entropy']['params']
ni=data['negative']['incomingModel']['entropy']['params']
no=data['negative']['outgoingModel']['entropy']['params']

f=open('entropy.csv', 'w')
f.write("pim pis pom pos nim nis nom nos\n")
print(pi, po, ni, no)
vals=pi+po+ni+no
s=" ".join(map(str, vals))
f.write(s)
f.write("\n")
f.close()
