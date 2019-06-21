import abc
from mitxgraders.baseclasses import ObjectWithSchema

class CorrelatedComparer(ObjectWithSchema):
    """
    CorrelatedComparer are callable objects used as comparer functions
    in FormulaGrader problems. Unlike standard comparer functions, CorrelatedComparer
    are given access to all parameter evaluations at once.

    For example, a comparer function that decides whether the student input is a
    nonzero constant multiple of the expected input would need to be a correlated
    comparer so that it can determine if there is a linear relationship between
    the student and expected samples.

    This class is abstract. Correlated Comparers should inherit from it.
    """

    # This is an abstract base class
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __call__(self, comparer_params_evals, student_evals, utils):
        pass
