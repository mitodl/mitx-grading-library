import numpy as np

try:
    # Prior to version 1.13, numpy added an extra space before floats when printing arrays
    # We use 1.6 for Python 2 and 1.16 for Python 3, so the printing difference
    # causes problems for doctests.
    #
    # Setting the printer to legacy 1.13 combined with the doctest directive
    # NORMALIZE_WHITESPACE is fixes the issue.
    np.set_printoptions(legacy='1.13')
    body = "# Setting numpy to print in legacy mode"
    msg = "{header}\n{body}\n{footer}".format(header='#'*40, footer='#'*40, body=body)
    print(msg)
except TypeError:
    pass
