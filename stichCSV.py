import os

def parse(line):
  if ' ' in line:
    s=line.split(' ')[1]
    f=float(s)
    if f!=0:
      return s
    else:
     return None
  else:
    return None

if not os.path.exists('summaries'):
  os.mkdir('summaries')

for dataset in os.listdir('graphs'):
  for protocol in os.listdir('graphs/'+dataset):
    if not os.path.exists('summaries/'+protocol):
      os.mkdir('summaries/'+protocol)
    for feature in ['duration']:
      f=open('graphs/'+dataset+'/'+protocol+'/'+feature+'_data.csv')
      s=f.read()
      f.close()
      lines=s.split("\n")
      data=filter(lambda x: x!=None, map(parse, lines))
      f=open('summaries/'+protocol+'/summarize_'+feature+'.r', 'a')
      f.write("read.csv('/Users/brandon/AdversaryLab-offline/graphs/"+dataset+"/"+protocol+"/"+feature+"_data.csv')\n")
      f.close()

