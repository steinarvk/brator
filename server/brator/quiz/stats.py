import cmath
import math

import beeline

MIN_DATA_POINTS = 5
MAX_DATA_POINTS_EXACT = 50

MIN_PROBABILITY = 0.001
MAX_PROBABILITY = (1 - MIN_PROBABILITY)

def _clamp_probability(p):
    if p < MIN_PROBABILITY:
        return MIN_PROBABILITY
    if p > MAX_PROBABILITY:
        return MAX_PROBABILITY
    return p

@beeline.traced(name="poisson_binomial_dft_pmf")
def poisson_binomial_dft_pmf(ps, k):
  n = len(ps)
  ps = [float(p) for p in ps]
  if k < 0:
      return 0
  if k > n:
      return 0
  if k != int(k):
      return 0
  C = cmath.exp( 2j * math.pi / (1+len(ps)))
  rv = 0
  for l in range(len(ps)+1):
    clk = C**(-l * k)
    el = 1
    for m in range(1, len(ps)+1):
      p = ps[m-1]
      el *= 1 + p * (C**l - 1)
    rv += clk * el
  return rv.real / (len(ps) + 1)

@beeline.traced(name="calculate_plausibility_of")
def calculate_plausibility_of(confidence_correctness):
    if len(confidence_correctness) < MIN_DATA_POINTS:
        return None

    if len(confidence_correctness) > MAX_DATA_POINTS_EXACT:
        return None

    probs = []
    corrs = []

    for conf, correctness in confidence_correctness:
        if not (0 <= conf <= 1):
            raise ValueError(f"bad confidence: {conf}")
        if correctness not in (True, False, 0, 1):
            raise ValueError(f"bad correctness: {correctness}")
        probs.append(float(_clamp_probability(conf)))
        corrs.append(int(correctness))

    pmfs = []

    num_correct = sum(corrs)

    for k in range(0, len(probs)+1):
        pmfs.append(poisson_binomial_dft_pmf(probs, k))

    prob_same = pmfs[num_correct]

    if num_correct == 0:
        prob_fewer = 0
        prob_more = 1 - prob_same
    elif num_correct == len(probs):
        prob_more = 0
        prob_fewer = 1 - prob_same
    else:
        prob_fewer = sum(pmfs[:num_correct])
        prob_more = sum(pmfs[num_correct+1:])

    return {
        "method": "poisson-binomial-dft-pmf",
        "prob_fewer": prob_fewer,
        "prob_same": prob_same,
        "prob_more": prob_more,
    }
