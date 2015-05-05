data {
  int<lower=1> N; // number of samples
  real<lower=0> samples[N];
}

parameters {
  real alpha;
  real beta;
}

model {
  alpha ~ normal(0, 0.001);
  beta ~ normal(0, 0.001);

  for(n in 1:(N-1))
    samples[n] ~ gamma(alpha, beta);
}
