import os
import json
import glob

from PIL import Image
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
      if z==1: # Certain
        pixels[y,x] = (255, 255, 255)
      elif z==0: # Impossible
        pixels[y,x] = (0, 0, 0)
      elif z<0.00195: # Unlikely
        pixels[y,x] = (150, 0, 250)
      elif z<0.0078: # Approximately uniform
        pixels[y,x] = (0, 0, 255)
      elif z<0.007: # More likely than uniform
        pixels[y,x] = (0, 255, 0)
      elif z<0.5: # Less likeley than not
        pixels[y,x] = (255, 255, 0)
      elif z<0.9: # More likely than not
        pixels[y,x] = (255, 69, 0)
      else: # Extremely likely
        pixels[y,x] = (255, 0, 0)

#  img.show()
  img.save('seq-graphs/'+protocol+'-'+direction+'.bmp')

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
