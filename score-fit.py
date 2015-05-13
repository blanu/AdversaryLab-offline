import sys

def readCSV(filename):
  f=open(filename)
  data=f.read()
  f.close()

  result={}
  lines=data.split("\n")
  names=lines[0].strip().split(' ')
  for name in names:
    result[name]=[]
  for line in lines[1:]:
    line=line.strip()
    if line=='':
      break
    items=line.split(' ')
    for x in range(len(names)):
      result[names[x]].append(items[x])
  return result

def predict(a, b):
  if a=='NA' or b=='NA':
    return 0
  elif a>b:
    return 1
  elif a<b:
    return -1
  else:
    return 0

def truePositives(actualPositives):
  return map(lambda x: x==1, actualPositives)

def falsePositives(actualNegatives):
  return map(lambda x: x==1, actualNegatives)

def trueNegatives(actualNegatives):
  return map(lambda x: x==-1, actualNegatives)

def falseNegatives(actualPositives):
  return map(lambda x: x==-1, actualPositives)

def undecided(items):
  return map(lambda x: x==0, items)

def summarize(httpPos, httpNeg, httpsPos, httpsNeg):
  predHttp=[predict(x,y) for x,y in zip(httpPos,httpNeg)]
  predHttps=[predict(x,y) for x,y in zip(httpsPos,httpsNeg)]

  return correctness(predHttp, predHttps)

def correctness(predHttp, predHttps):
  totalp=len(predHttp)
  totaln=len(predHttps)
  total=totalp+totaln

  tp=truePositives(predHttp)
  fn=falseNegatives(predHttp)
  uap=undecided(predHttp)
  fp=falsePositives(predHttps)
  tn=trueNegatives(predHttps)
  uan=undecided(predHttps)

  return map(lambda x: x*100, [sum(tp)/totalp, sum(fn)/totalp, sum(uap)/totalp, sum(tn)/totaln, sum(fp)/totaln, sum(uan)/totaln])

def printLegend():
  print(["Adversary", "Feature", "Direction", "True Pos", "False Neg", "Unknown", "True Neg", "False Pos", "Unknown"])

def plotFeature(ad, direction, feature, label, pdata, ndata, pdata2, ndata2):
#  pdf(paste('/Users/brandon/AdversaryLab-offline/scores/raw-', ad, '-', direction, '-', feature, '.pdf', sep=""))
  summary=summarize(pdata, ndata, pdata2, ndata2)
  print(ad, feature, direction, summary, rate(summary))

def rate(summary):
  if (summary[0]==0 and summary[1]==0 and summary[2]==0) or (summary[3]==0 and summary[4]==0 and summary[5]==0):
    return 'Error'
  else:
    if summary[0]>summary[1] and summary[3]>summary[4]:
      if summary[2]==0 and summary[5]==0:
        return 'Excellent'
      else:
        return 'Good'
    else:
      return 'Bad'

"""
totalScore=function(table)
{
  d=mapply(predict, table$positiveDuration, table$negativeDuration)

  ic=mapply(predict, table$positiveIncomingContent, table$negativeIncomingContent)
  oc=mapply(predict, table$positiveOutgoingContent, table$negativeOutgoingContent)

  ifl=mapply(predict, table$positiveIncomingFlow, table$negativeIncomingFlow)
  ofl=mapply(predict, table$positiveOutgoingFlow, table$negativeOutgoingFlow)

  ie=mapply(predict, table$positiveIncomingEntropy, table$negativeIncomingEntropy)
  oe=mapply(predict, table$positiveOutgoingEntropy, table$negativeOutgoingEntropy)

  il=mapply(predict, table$positiveIncomingLength, table$negativeIncomingLength)
  ol=mapply(predict, table$positiveOutgoingLength, table$negativeOutgoingLength)

  d+ic+oc+ifl+ofl+ie+oe+il+ol
}

plotTotal=function(pos, neg, title)
{
  pdf('/Users/brandon/AdversaryLab-offline/scores/total.pdf')

  barplot(correctness(totalScore(http), totalScore(https)), main="Total Score", ylab="Percent", names.arg=c("True Pos", "False Neg", "Unknown", "True Neg", "False Pos", "Unknown"))
  dev.off()
}

flatten=function(x)
{
  if(x>0)
  {
    1
  }
  else
  {
    if(x<0)
    {
      -1
    }
    else
    {
      0
    }
  }
}

totalScoreTorHTTPS=function(table)
{
  oe=mapply(predict, table$positiveoutgoingentropy, table$negativeoutgoingentropy)

  is=mapply(predict, table$positiveincomingsequence, table$negativeincomingsequence)
  os=mapply(predict, table$positiveoutgoingsequence, table$negativeoutgoingsequence)

  total=oe+is+os

  mapply(flatten, total)
}

plotTotalTorHTTPS=function(pos, neg, title)
{
  pdf('/Users/brandon/AdversaryLab-offline/scores/Tor-HTTPS-total.pdf')

  barplot(correctness(totalScoreTorHTTPS(http), totalScoreTorHTTPS(https)), main=title, ylab="Percent", names.arg=c("True Pos", "False Neg", "Unknown", "True Neg", "False Pos", "Unknown"))
  dev.off()
}

totalScoreRTSPTor=function(table)
{
  oc=mapply(predict, table$positiveoutgoingcontent, table$negativeoutgoingcontent)

  ie=mapply(predict, table$positiveincomingentropy, table$negativeincomingentropy)
  oe=mapply(predict, table$positiveoutgoingentropy, table$negativeoutgoingentropy)

#  il=mapply(predict, table$positiveincominglength, table$negativeincominglength)
#  ol=mapply(predict, table$positiveoutgoinglength, table$negativeoutgoinglength)

  is=mapply(predict, table$positiveincomingsequence, table$negativeincomingsequence)
  os=mapply(predict, table$positiveoutgoingsequence, table$negativeoutgoingsequence)

  total=oc+ie+oe+is+os

  mapply(flatten, total)
}

plotTotalRTSPTor=function(pos, neg, title)
{
  pdf('/Users/brandon/AdversaryLab-offline/scores/RTSP-Tor-total.pdf')

  barplot(correctness(totalScoreRTSPTor(http), totalScoreRTSPTor(https)), main=title, ylab="Percent", names.arg=c("True Pos", "False Neg", "Unknown", "True Neg", "False Pos", "Unknown"))
  dev.off()
}
"""

adversary=sys.argv[1]
parts=adversary.split('-')
positive=parts[0]
negative=parts[1]

http=readCSV('/Users/brandon/AdversaryLab-offline/scores/fit-'+adversary+'-'+positive+'.csv')
https=readCSV('/Users/brandon/AdversaryLab-offline/scores/fit-'+adversary+'-'+negative+'.csv')

printLegend()

plotFeature(adversary, 'incoming', 'content', 'Incoming Content', http['positiveincomingcontent'], http['negativeincomingcontent'], https['positiveincomingcontent'], https['negativeincomingcontent'])
plotFeature(adversary, 'outgoing', 'content', 'Outgoing Content', http['positiveoutgoingcontent'], http['negativeoutgoingcontent'], https['positiveoutgoingcontent'], https['negativeoutgoingcontent'])

plotFeature(adversary, 'incoming', 'entropy', 'Incoming Entropy', http['positiveincomingentropy'], http['negativeincomingentropy'], https['positiveincomingentropy'], https['negativeincomingentropy'])
plotFeature(adversary, 'outgoing', 'entropy', 'Outgoing Entropy', http['positiveoutgoingentropy'], http['negativeoutgoingentropy'], https['positiveoutgoingentropy'], https['negativeoutgoingentropy'])

plotFeature(adversary, 'incoming', 'flow', 'Incoming Flow', http['positiveincomingflow'], http['negativeincomingflow'], https['positiveincomingflow'], https['negativeincomingflow'])
plotFeature(adversary, 'outgoing', 'flow', 'Outgoing Flow', http['positiveoutgoingflow'], http['negativeoutgoingflow'], https['positiveoutgoingflow'], https['negativeoutgoingflow'])

plotFeature(adversary, 'incoming', 'length', 'Incoming Length', http['positiveincominglength'], http['negativeincominglength'], https['positiveincominglength'], https['negativeincominglength'])
plotFeature(adversary, 'outgoing', 'length', 'Outgoing Length', http['positiveoutgoinglength'], http['negativeoutgoinglength'], https['positiveoutgoinglength'], https['negativeoutgoinglength'])

plotFeature(adversary, 'incoming', 'sequence', 'Incoming Sequence', http['positiveincomingsequence'], http['negativeincomingsequence'], https['positiveincomingsequence'], https['negativeincomingsequence'])
plotFeature(adversary, 'outgoing', 'sequence', 'Outgoing Sequence', http['positiveoutgoingsequence'], http['negativeoutgoingsequence'], https['positiveoutgoingsequence'], https['negativeoutgoingsequence'])

"""
plotTotal(http, https, "Total Score")

plotTotalTorHTTPS(http, https, "Tor vs HTTPS")

plotTotalRTSPTor(http, https, "RTSP vs Tor")
"""
