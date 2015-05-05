data {
  int<lower=0> counts[1440];
}

parameters {
  simplex[1440] alpha;
  simplex[1440] theta;
}

model {
  theta ~ dirichlet(alpha);
  counts ~ multinomial(theta);
}
