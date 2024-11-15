"""
defaults_sample.py

This plug-in can be used to set course-wide defaults for a given grading class.

We recommend copying this file (so that upgrading the library won't overwrite it),
renaming it to defaults.py, and modifying it according to your needs.

This plug-in works by registering a dictionary with the appropriate grading class (note,
not class instance).
"""
# from __future__ import print_function, division, absolute_import, unicode_literals

# # Here are all of the graders that you can specify defaults for
# from mitxgraders.stringgrader import StringGrader
# from mitxgraders.baseclasses import AbstractGrader, ItemGrader
# from mitxgraders.listgrader import ListGrader, SingleListGrader
# from mitxgraders.formulagrader.integralgrader import IntegralGrader
# from mitxgraders.formulagrader.formulagrader import FormulaGrader, NumericalGrader
# from mitxgraders.formulagrader.matrixgrader import MatrixGrader

# # These will be needed to set attempt-based credit course-wide
# from mitxgraders.attemptcredit import LinearCredit, GeometricCredit, ReciprocalCredit

# These modifications are commented out so that they don't override the normal defaults.
# To use them, you need to uncomment them.

# Change case_sensitive to False by default
# StringGrader.register_defaults({
#     'case_sensitive': False
# })

# Turn on attempt-based partial credit by default and modify related settings
# This will turn on attempt-based partial credit for all graders
# AbstractGrader.register_defaults({
#     'attempt_based_credit': ReciprocalCredit(),
#     'attempt_based_credit_msg': True
# })
# Note that if you do this, you will need to either pass cfn_extra_args="attempt" in every
# customresponse tag or explicitly disable attempt-based credit.

# Note that registered defaults can be applied to a higher level class than where those
# options normally live. For example, to turn on debug by default in all StringGrader
# instances (debug is defined in AbstractGrader), you can do the following:
# StringGrader.register_defaults({
#     'debug': True
# })

# Precedence is given to the registered defaults of higher level classes. If
# register_defaults is called twice on the same class, the options stack on top of
# each other, overwriting earlier options as necessary.

# In this example, we make all MatrixGrader problems award partial credit by default.
# MatrixGrader.register_defaults({
#     'entry_partial_credit': 'partial'
# })

# You can also use this plug-in to make pre-built graders and functions available to
# all your problems. You just need to include them in the __all__ list. For example:
# my_grader = FormulaGrader(variables=['x', 'y'])
# __all__ = ['my_grader']
# Now, "from mitxgraders import *"" will make my_grader available to you in a problem
# You can similarly define custom functions etc, in the same way.
