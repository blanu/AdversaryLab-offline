import os
import glob
import shutil

files=glob.glob('*.pcap')
for file in files:
  file=file.split('.')[0]
  if file and file!='':
    parts=file.split('-')
    #sorted-92-HTTPS-UAE.pcap
    id=parts[1]
    protocol=parts[2]
    dataset=parts[3]

    if not os.path.exists(dataset):
      os.mkdir(dataset)
    if not os.path.exists(dataset+'/'+protocol):
      os.mkdir(dataset+'/'+protocol)
    if not os.path.exists('ALL'):
      os.mkdir('ALL')
    if not os.path.exists('ALL/HTTP'):
      os.mkdir('ALL/HTTP')
    if not os.path.exists('ALL/HTTPS'):
      os.mkdir('ALL/HTTPS')
    shutil.copyfile(file+'.pcap', 'ALL/'+protocol+'/'+id)
    shutil.move(file+'.pcap', dataset+'/'+protocol+'/'+id)
