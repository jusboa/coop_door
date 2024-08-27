import pytest
import math

from ..coop_door.filter import Filter

@pytest.fixture
def default_coefficient():
    return 0.1

@pytest.fixture
def filter(default_coefficient):
    return Filter(default_coefficient)

@pytest.fixture
def sample_time():
    # just a dummy value, it cancels out in
    # equations, but need to use a consistent value
    return 1

def coefficient_to_tau(coefficient, sample_time):
    return -sample_time / math.log(1 - coefficient)

def number_of_samples(time, sample_time):
    return round(time / sample_time)

def number_of_samples(coefficient):
    return round(-1 / math.log(1 - coefficient))

def test_nan_after_init(filter):
    assert math.isnan(filter.output())

def test_first_sample_is_output(filter):
    x = 1.25
    filter.sample(x)
    assert math.isclose(filter.output(), x)

def test_sample_function_returns_current_output(filter):
    x = 0.36
    assert math.isclose(filter.sample(x), x)

def test_response_to_dc_signal(filter):
    x = 5.1
    for _ in range(1000):
        filter.sample(x)
    assert math.isclose(filter.output(), x)

def test_step_response_at_time_tau(filter, default_coefficient):
    x = 0
    filter.sample(x)
    x = 1

    for _ in range(number_of_samples(default_coefficient)):
        filter.sample(x)

    assert math.isclose(filter.output(), 0.632, rel_tol=0.05)

def test_step_response_at_time_tau(filter, default_coefficient):
    x = 0
    filter.sample(x)
    x = 1
    for _ in range(5 * number_of_samples(default_coefficient)):
        filter.sample(x)

    assert math.isclose(filter.output(), 0.993, rel_tol=0.05)

def test_set_coefficient(filter, default_coefficient):
    assert math.isclose(default_coefficient, filter.coefficient())
    k = 0.25
    filter.set_coefficient(k)
    assert filter.coefficient() == k

def test_change_coefficient_filter_changes_accordingly(filter, default_coefficient):
    k = default_coefficient / 10
    filter.set_coefficient(k)

    # sample unit step for another tau
    x = 0
    filter.sample(x)
    x = 1
    for _ in range(number_of_samples(k)):
        filter.sample(x)
    # the output corresponds to a new coefficient
    assert math.isclose(filter.output(), 0.632, rel_tol=0.05)
    
def test_no_coefficient_no_filtering(filter):
    filter.set_coefficient(1)
    filter.sample(0)
    assert filter.sample(1) == 1

def test_nan_after_reset(filter):
    filter.sample(1)
    filter.reset()
    assert math.isnan(filter.output())

def test_reset_restarts_filtering(filter, default_coefficient):
    # sample unit step for one tau
    x = 0
    filter.sample(x)
    x = 1
    for _ in range(number_of_samples(default_coefficient)):
        filter.sample(x)

    filter.reset()

    # sample unit step for another tau
    x = 0
    filter.sample(x)
    x = 1
    for _ in range(number_of_samples(default_coefficient)):
        filter.sample(x)
    # the output corresponds to one tau only
    assert math.isclose(filter.output(), 0.632, rel_tol=0.05)
