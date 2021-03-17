import decimal

from .stats import poisson_binomial_dft_pmf

def test_poisson_binomial_df_pmf():
    xs = [0.5, 0.5, 0.5]
    epsilon = 1e-6
    assert (poisson_binomial_dft_pmf(xs, 0) - 0.125) < epsilon
    assert (poisson_binomial_dft_pmf(xs, 1) - 0.375) < epsilon
    assert (poisson_binomial_dft_pmf(xs, 2) - 0.375) < epsilon
    assert (poisson_binomial_dft_pmf(xs, 3) - 0.125) < epsilon

def test_poisson_binomial_df_pmf_decimals():
    xs = [decimal.Decimal(x) for x in [0.5, 0.5, 0.5]]
    epsilon = 1e-6
    assert (poisson_binomial_dft_pmf(xs, 0) - 0.125) < epsilon
    assert (poisson_binomial_dft_pmf(xs, 1) - 0.375) < epsilon
    assert (poisson_binomial_dft_pmf(xs, 2) - 0.375) < epsilon
    assert (poisson_binomial_dft_pmf(xs, 3) - 0.125) < epsilon

