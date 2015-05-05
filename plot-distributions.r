plotDuration=function(adversary, model)
{
  pdf(paste('/Users/brandon/AdversaryLab-offline/dist-graphs/', adversary, '-duration', '.pdf', sep=""))
  pd=model$positive$duration$params
  nd=model$negative$duration$params
  px <- rexp(1000, pd)
  nx <- rexp(1000, nd)
  plot(sort(px), col="blue", main="Duration", ylab="Seconds", xlab="Index")
  points(sort(nx), col="red")
  dev.off()
}

plotEntropy=function(adversary, pd, title, side, direction, color, min)
{
  pdf(paste('/Users/brandon/AdversaryLab-offline/dist-graphs/', adversary, '-entropy', '-', side, '-', direction, '.pdf', sep=""))
  x <- seq(min, 8, length=100)
  px <- dnorm(x, pd[1], pd[2])
  nx <- dnorm(x, nd[1], nd[2])
  plot(x, px, col=color, main=title, ylab="Probability Density", xlab="Entropy")
  dev.off()
}

plotContent=function(adversary, pd, nd, title, direction)
{
  pdf(paste('/Users/brandon/AdversaryLab-offline/dist-graphs/', adversary, '-content', '-', direction, '.pdf', sep=""))
  plot(pd, col="blue", main=title, ylab="Probability Density", xlab="Byte Index", ylim=c(0.003, 0.008))
  points(nd, col="red")
  dev.off()
}

plotLength=function(adversary, pd, nd, title, direction)
{
  pdf(paste('/Users/brandon/AdversaryLab-offline/dist-graphs/', adversary, '-length', '-', direction, '.pdf', sep=""))
  plot(pd, col="blue", main=title, ylab="Probability Density", xlab="Packet Length")
  points(nd, col="red")
  dev.off()
}

plotFlow=function(adversary, pd, nd, title, direction)
{
  pdf(paste('/Users/brandon/AdversaryLab-offline/dist-graphs/', adversary, '-flow', '-', direction, '.pdf', sep=""))
  px <- rpois(1000, pd)
  nx <- rpois(1000, nd)
  plot(sort(px), col="blue", main="Flow", ylab="Packets", xlab="Index")
  points(sort(nx), col="red")
  dev.off()
}

model=fromJSON(file='/Users/brandon/AdversaryLab-offline/adversaries/Tor-HTTPS/model')
plotDuration('Tor-HTTPS', model)

plotEntropy('Tor-HTTPS', model$positive$incomingModel$entropy$params, 'Tor Incoming Entropy', 'Tor', 'incoming', 'blue', 7.98)
plotEntropy('Tor-HTTPS', model$negative$incomingModel$entropy$params, 'HTTPS Incoming Entropy', 'HTTPS', 'incoming', 'red', 6)
plotEntropy('Tor-HTTPS', model$positive$outgoingModel$entropy$params, 'Tor Outgoing Entropy', 'Tor', 'outgoing', 'blue', 7.99)
plotEntropy('Tor-HTTPS', model$negative$outgoingModel$entropy$params, 'HTTPS Outgoing Entropy', 'HTTPS', 'outgoing', 'red', 6)

plotContent('Tor-HTTPS', model$positive$incomingModel$content$params, model$negative$incomingModel$content$params, 'Incoming Content', 'incoming')
plotContent('Tor-HTTPS', model$positive$outgoingModel$content$params, model$negative$outgoingModel$content$params, 'Outgoing Content', 'outgoing')

plotLength('Tor-HTTPS', model$positive$incomingModel$length$params, model$negative$incomingModel$length$params, 'Incoming Length', 'incoming')
plotLength('Tor-HTTPS', model$positive$outgoingModel$length$params, model$negative$outgoingModel$length$params, 'Outgoing Length', 'outgoing')

plotFlow('Tor-HTTPS', model$positive$incomingModel$flow$params, model$negative$incomingModel$flow$params, 'Incoming Flow', 'incoming')
plotFlow('Tor-HTTPS', model$positive$outgoingModel$flow$params, model$negative$outgoingModel$flow$params, 'Outgoing Flow', 'outgoing')
