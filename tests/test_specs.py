"""
Tests written based on the library documentation
"""
from graders import ListGrader, StringGrader, FormulaGrader

##############
# ListGrader #
##############
def test_eigensystem():
    """
    Tests the eigensystem example

    TODO Change to NumericalGrader when it gets implemented
    """
    grader = ListGrader(
        answers=[
            ['1', (['1', '0'], ['-1', '0'])],
            ['-1', (['0', '1'], ['0', '-1'])],
        ],
        subgraders=ListGrader(
            subgraders=[
                FormulaGrader(),
                ListGrader(
                    subgraders=FormulaGrader()
                )
            ],
            ordered=True,
            grouping=[1, 2, 2]
        ),
        grouping=[1, 1, 1, 2, 2, 2]
    )

    expected_result = {
        'overall_message': '',
        'input_list': [
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''},
            {'ok': True, 'grade_decimal': 1, 'msg': ''}
        ]
    }
    submissions = ['1', '-1', '0', '-1', '0', '1']
    assert grader(None, submissions) == expected_result
