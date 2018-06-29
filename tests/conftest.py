from mitxgraders.sampling import set_seed

def pytest_runtest_setup(item):
    """called before ``pytest_runtest_call(item)."""
    print("Resetting random.seed and numpy.random.seed for test {item}".format(item=item))
    set_seed()
