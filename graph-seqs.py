import json

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt

def splitData(data):
  xs=[]
  ys=[]
  zs=[]

  for y in range(len(data)):
    for x in range(len(data[y])):
      z=data[y][x]
      xs.append(x)
      ys.append(y)
      zs.append(z)
  return (xs, ys, zs)

f=open('seqs/protocols/HTTPRSS')
data=f.read()
f.close()

data=json.loads(data)
xs, ys, zs=splitData(data['incoming'])

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.bar3d(xs, ys, zs)
plt.savefig('HTTPRSS-incoming.pdf')
