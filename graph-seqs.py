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
      pixels[y,x] = convert5(z)

  img.show()
  img.save('seq-graphs/'+protocol+'-'+direction+'.bmp')

def convert(z):
  if z==1: # Certain - White
    return (255, 255, 255)
  elif z==0: # Impossible - Black
    return (0, 0, 0)
  elif z<=1.0/512.0: # Unlikely - Purple
    return (150, 0, 250)
  elif z<=1.0/127.0: # Approximately uniform - Blue
    return (0, 0, 255)
  elif z<=0.5: # More likely than uniform - Green
    return (0, 255, 0)
  else: # Extremely likely - Red
    return (255, 0, 0)

def convert2(z):
  zz=rescale(z)
  if zz==0:
    return (0, 0, 0)
  elif zz==1:
    return (255, 255, 255)
  else:
    r, g, b = colorsys.hsv_to_rgb((1-zz)*(2.0/3.0), 0.5, 1)
    return (int(r*255), int(g*255), int(b*255))

def convert3(z):
  zz=rescale2(z)
  if zz==0:
    return (0, 0, 0)
  elif zz==1:
    return (255, 255, 255)
  else:
    r, g, b = colorsys.hsv_to_rgb((1-zz)*(2.0/3.0), 0.5, 1)
    return (int(r*255), int(g*255), int(b*255))

def rescale(z):
  bottom=1.0/256.0
  top=1-bottom
  if z==0:
    return 0
  elif z==1:
    return 1
  elif z==bottom:
    return 0.5
  elif z>bottom:
    return (((z-bottom)/top)*0.5)+0.5
  else:
    return (z/bottom)*0.5

def rescale2(z):
  if z==0:
    return 0
  elif z==1:
    return 1
  else:
    return z ** (1.0/8.0)

def convert4(z):
  zz=z
  if zz==0:
    return (0, 0, 0)
  elif zz==1:
    return (255, 255, 255)
  else:
    r, g, b = colorsys.hsv_to_rgb((1-zz)*(2.0/3.0), 0.5, 1)
    return (int(r*255), int(g*255), int(b*255))

def convert5(z):
  if z==1: # Certain - White
    return (255, 255, 255)
  elif z==0: # Impossible - Black
    return (0, 0, 0)
  elif z<=0.1/256.0: # Unlikely - Purple
    return (150, 0, 250)
  elif z<=10.0/256.0: # Approximately uniform - Blue
    return (0, 0, 255)
  elif z<=0.5: # More likely than uniform - Green
    return (0, 255, 128)
  else: # Extremely likely - Red
    return (255, 0, 0)

if not os.path.exists('seq-graphs'):
  os.mkdir('seq-graphs')
for protocol in os.listdir('seqs/protocols'):
  print('Loading %s...' % (protocol))
  f=open('seqs/protocols/'+protocol)
  data=f.read()
  f.close()

  print('Parsing...')
  data=json.loads(data)
  print('Splitting...')
  graph(data['incoming'], 'incoming', protocol)
  graph(data['outgoing'], 'outgoing', protocol)
