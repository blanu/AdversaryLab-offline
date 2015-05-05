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

print('Loading...')
f=open('seqs/protocols/HTTPRSS')
data=f.read()
f.close()

print('Parsing...')
data=json.loads(data)
print('Splitting...')
xs, ys, zs=splitData(data['incoming'])
rgb=plt.get_cmap('jet')(zs)

print('Plotting...')
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ax.scatter(xs, ys, color=rgb)
plt.show()
#plt.savefig('HTTPRSS-incoming.pdf')
