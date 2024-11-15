"""
Tests of validatorfuncs.py
"""
from __future__ import print_function, division, absolute_import

from pytest import raises
from voluptuous import Invalid, truth, Schema
from mitxgraders import RandomFunction
from mitxgraders.helpers import validatorfuncs

def test_validators():
    """Tests of validatorfuncs.py that aren't covered elsewhere"""
    # PercentageString
    with raises(Invalid, match="Not a valid percentage string"):
        validatorfuncs.PercentageString("mess%")

    # ListOfType
    testfunc = validatorfuncs.ListOfType(int)
    assert testfunc([1, 2, 3]) == [1, 2, 3]

    # TupleOfType
    @truth
    def testvalidator(obj):
        """Returns true"""
        return True
    testfunc = validatorfuncs.TupleOfType(int, testvalidator)
    assert testfunc((-1,)) == (-1,)

def test_argument_number_of_RandomFunction():
    """Tests to make sure we can extract the number of inputs expected for a random function"""
    func = RandomFunction(input_dim=3).gen_sample()
    assert validatorfuncs.get_number_of_args(func) == 3
