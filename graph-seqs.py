import os
import json

import Image
import colorsys

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

def graph(data, direction, protocol):
  ymax=len(data)
  xmax=len(data[0])

  img = Image.new( 'RGB', (ymax,xmax), "black") # create a new black image
  pixels = img.load() # create the pixel map

  for y in range(ymax):    # for every pixel:
    for x in range(xmax):
      z=data[y][x]
      if z==1:
        pixels[y,x] = (255, 255, 255)
      elif z==0:
        pixels[y,x] = 0
      else:
        r, g, b = colorsys.hsv_to_rgb(z*(2.0/3.0), 1.0, 1.0)
        pixels[y,x] = (int(r*255), int(g*255), int(b*255))

#  img.show()
  img.save('seq-graphs/'+protocol+'-'+direction+'.png')

if not os.path.exists('seq-graphs'):
  os.mkdir('seq-graphs')
for protocol in os.listdir('seqs/protocols'):
  print('Loading...')
  f=open('seqs/protocols/'+protocol)
  data=f.read()
  f.close()

  print('Parsing...')
  data=json.loads(data)
  print('Splitting...')
  graph(data['incoming'], 'incoming', protocol)
  graph(data['outgoing'], 'outgoing', protocol)
