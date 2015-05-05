data {
  int<lower=1> N;
  real<lower=0, upper=1440> samples[N];
}

parameters {
  real theta;
  real sigma;
}

model {
  for(n in 1:(N-1))
    samples[n] ~ normal(theta, sigma);
}
