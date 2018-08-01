from functools import wraps

def log_results(results):
    """
    Generate a decorator that logs function calls to results.

    Arguments:
        results: list into which results are logged
    Returns:
        Decorator that logs result of each call to function to results

    Usage:
    >>> results = []
    >>> @log_results(results)
    ... def f(x, y):
    ...     return x + y
    >>> f(2, 3); f(20, 30);
    5
    50
    >>> results
    [5, 50]
    """

    def make_decorator(results):
        def decorator(func):
            @wraps(func)
            def _func(*args, **kwargs):
                result = func(*args,**kwargs)
                results.append(result)
                return result

            return _func
        return decorator

    return make_decorator(results)
