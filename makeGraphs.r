readData=function(dataset, protocol, feature) {
  return read.csv('/Users/brandon/AdversaryLab-offline/graphs/'+dataset+'/'+protocol+'/'+feature+'_data.csv')
}

johttp=readData('JO', 'HTTP', 'duration')
