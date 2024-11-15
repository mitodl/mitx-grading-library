"""
Tests for the various sampling classes
"""
from __future__ import print_function, division, absolute_import

from itertools import product
import numpy as np
from pytest import raises, approx
import six

from mitxgraders import (
    RealVectors,
    ComplexVectors,
    RealTensors,
    ComplexTensors,
    RealMatrices,
    ComplexMatrices,
    IdentityMatrixMultiples,
    SquareMatrices,
    OrthogonalMatrices,
    UnitaryMatrices,
    MathArray,
    RealInterval,
    ComplexRectangle,
    ConfigError
)
from mitxgraders.helpers.calc import within_tolerance

def test_vectors():
    # Test shape, real/complex, norm, MathArray
    shapes = tuple(range(2, 5))
    norms = ([2, 6], [3, 4], [4, 12], [1 - 1e-12, 1 + 1e-12])

    for shape in shapes:
        for norm in norms:
            vectors = RealVectors(shape=shape, norm=norm)
            vec = vectors.gen_sample()
            assert vec.shape == (shape, )
            assert norm[0] <= np.linalg.norm(vec) <= norm[1]
            assert np.array_equal(np.conj(vec), vec)
            assert isinstance(vec, MathArray)

            vectors = ComplexVectors(shape=shape, norm=norm)
            vec = vectors.gen_sample()
            assert vec.shape == (shape, )
            assert norm[0] <= np.linalg.norm(vec) <= norm[1]
            assert not np.array_equal(np.conj(vec), vec)
            assert isinstance(vec, MathArray)

def test_tensors():
    # Test shape, real/complex, norm, MathArray
    shapes = product(tuple(range(2, 4)), tuple(range(3, 5)), tuple(range(1, 5)))
    norms = ([2, 6], [3, 4], [4, 12], [1 - 1e-12, 1 + 1e-12])

    for shape in shapes:
        for norm in norms:
            tensors = RealTensors(shape=shape, norm=norm)
            t = tensors.gen_sample()
            assert t.shape == shape
            assert norm[0] <= np.linalg.norm(t) <= norm[1]
            assert np.array_equal(np.conj(t), t)
            assert isinstance(t, MathArray)

            tensors = ComplexTensors(shape=shape, norm=norm)
            t = tensors.gen_sample()
            assert t.shape == shape
            assert norm[0] <= np.linalg.norm(t) <= norm[1]
            assert not np.array_equal(np.conj(t), t)
            assert isinstance(t, MathArray)

def test_general_matrices():
    # Test shape, real/complex, norm, triangular options, MathArray
    shapes = product(tuple(range(2, 5)), tuple(range(2, 5)))
    norms = ([2, 6], [3, 4], [4, 12], [1 - 1e-12, 1 + 1e-12])
    triangles = (None, 'upper', 'lower')

    for shape in shapes:
        for norm in norms:
            for triangle in triangles:
                matrices = RealMatrices(shape=shape, norm=norm, triangular=triangle)
                m = matrices.gen_sample()
                assert m.shape == shape
                assert norm[0] <= np.linalg.norm(m) <= norm[1]
                assert np.array_equal(np.conj(m), m)
                assert isinstance(m, MathArray)
                if triangle is None:
                    assert not within_tolerance(m, MathArray(np.triu(m)), 0)
                    assert not within_tolerance(m, MathArray(np.tril(m)), 0)
                elif triangle == "upper":
                    assert within_tolerance(m, MathArray(np.triu(m)), 0)
                elif triangle == "lower":
                    assert within_tolerance(m, MathArray(np.tril(m)), 0)

                matrices = ComplexMatrices(shape=shape, norm=norm, triangular=triangle)
                m = matrices.gen_sample()
                assert m.shape == shape
                assert norm[0] <= np.linalg.norm(m) <= norm[1]
                assert not np.array_equal(np.conj(m), m)
                assert isinstance(m, MathArray)
                if triangle is None:
                    assert not within_tolerance(m, MathArray(np.triu(m)), 0)
                    assert not within_tolerance(m, MathArray(np.tril(m)), 0)
                elif triangle == "upper":
                    assert within_tolerance(m, MathArray(np.triu(m)), 0)
                elif triangle == "lower":
                    assert within_tolerance(m, MathArray(np.tril(m)), 0)

def test_identity_multiples():
    # Test shape, identity times constant, MathArray
    shapes = tuple(range(2, 5))
    samples = ([-1, 1], RealInterval(), ComplexRectangle())

    for shape in shapes:
        for sample in samples:
            matrices = IdentityMatrixMultiples(dimension=shape, sampler=sample)
            m = matrices.gen_sample()
            assert m.shape == (shape, shape)
            assert np.array_equal(m, m[0, 0] * np.eye(shape))
            assert isinstance(m, MathArray)

def test_unitary():
    # Test shape, unitarity, determinant, MathArray
    # These are the doctests
    matrices = UnitaryMatrices()
    assert matrices.gen_sample().shape == (2, 2)

    matrices = UnitaryMatrices(dimension=4)
    assert matrices.gen_sample().shape == (4, 4)

    matrices = UnitaryMatrices(unitdet=True)
    assert within_tolerance(np.linalg.det(matrices.gen_sample()), 1, 1e-14)

    matrices = UnitaryMatrices(unitdet=False)
    assert not within_tolerance(np.linalg.det(matrices.gen_sample()), 1, 1e-14)
    assert within_tolerance(np.abs(np.linalg.det(matrices.gen_sample())), 1, 1e-14)

    matrices = UnitaryMatrices(unitdet=True)
    m = matrices.gen_sample()
    assert within_tolerance(m * np.conjugate(np.transpose(m)), MathArray(np.eye(2)), 1e-14)

    matrices = UnitaryMatrices(unitdet=False)
    m = matrices.gen_sample()
    assert within_tolerance(m * np.conjugate(np.transpose(m)), MathArray(np.eye(2)), 1e-14)

    shapes = tuple(range(2, 5))
    dets = (True, False)

    # More general testing
    for shape in shapes:
        for det in dets:
            matrices = matrices = UnitaryMatrices(dimension=shape, unitdet=det)
            m = matrices.gen_sample()
            assert m.shape == (shape, shape)
            assert within_tolerance(m * np.conjugate(np.transpose(m)), MathArray(np.eye(shape)), 1e-14)
            assert np.abs(np.linalg.det(m)) == approx(1)
            if det:
                assert np.linalg.det(m) == approx(1)
            assert isinstance(m, MathArray)

def test_orthogonal():
    # Test shape, orthogonality, determinant, MathArray
    # These are the doctests
    matrices = OrthogonalMatrices()
    assert matrices.gen_sample().shape == (2, 2)

    matrices = OrthogonalMatrices(dimension=4)
    assert matrices.gen_sample().shape == (4, 4)

    matrices = OrthogonalMatrices(unitdet=True)
    assert within_tolerance(np.linalg.det(matrices.gen_sample()), 1, 1e-14)

    matrices = OrthogonalMatrices(unitdet=False)
    m = matrices.gen_sample()
    assert (within_tolerance(np.linalg.det(m), 1, 1e-14)
            or within_tolerance(np.linalg.det(m), -1, 1e-14))

    matrices = OrthogonalMatrices(unitdet=True)
    m = matrices.gen_sample()
    assert within_tolerance(m * np.conjugate(np.transpose(m)), MathArray(np.eye(2)), 1e-14)

    matrices = OrthogonalMatrices(unitdet=False)
    m = matrices.gen_sample()
    assert within_tolerance(m * np.conjugate(np.transpose(m)), MathArray(np.eye(2)), 1e-14)

    shapes = tuple(range(2, 5))
    dets = (True, False)

    # More general testing
    for shape in shapes:
        for det in dets:
            matrices = matrices = OrthogonalMatrices(dimension=shape, unitdet=det)
            m = matrices.gen_sample()
            assert m.shape == (shape, shape)
            assert np.array_equal(np.conj(m), m)
            assert within_tolerance(m * np.transpose(m), MathArray(np.eye(shape)), 1e-14)
            assert (np.abs(np.linalg.det(m)) == approx(1)
                    or np.abs(np.linalg.det(m)) == approx(-1))
            if det:
                assert np.linalg.det(m) == approx(1)
            assert isinstance(m, MathArray)

def test_square_matrices():
    # Test shape, real/complex, norm, symmetry, traceless, det, MathArray
    shapes = tuple(range(2, 5))
    norms = ([2, 6], [1 - 1e-12, 1 + 1e-12])
    symmetries = (None, 'diagonal', 'symmetric', 'antisymmetric', 'hermitian', 'antihermitian')
    traceless_opts = (True, False)
    dets = (None, 0, 1)
    complexes = (True, False)

    for det, traceless, symmetry in product(dets, traceless_opts, symmetries):
        # Handle the cases that don't work
        if det == 0 and traceless:
            with raises(ConfigError, match='Unable to generate zero determinant traceless matrices'):
                SquareMatrices(traceless=traceless,
                               symmetry=symmetry,
                               determinant=det)
            continue

        # Continue with further cases
        for shape, norm, comp in product(shapes, norms, complexes):
            # Check for matrices that don't exist
            args = {'dimension': shape, 'norm': norm, 'traceless': traceless,
                    'symmetry': symmetry, 'determinant': det, 'complex': comp}
            if det == 1:
                if traceless and shape == 2:
                    if symmetry == 'diagonal' and not comp:
                        with raises(ConfigError, match='No real, traceless, unit-determinant, diagonal 2x2 matrix exists'):
                            SquareMatrices(**args)
                        continue
                    elif symmetry == 'symmetric' and not comp:
                        with raises(ConfigError, match='No real, traceless, unit-determinant, symmetric 2x2 matrix exists'):
                            SquareMatrices(**args)
                        continue
                    elif symmetry == 'hermitian':
                        with raises(ConfigError, match='No traceless, unit-determinant, Hermitian 2x2 matrix exists'):
                            SquareMatrices(**args)
                        continue
                elif shape % 2 == 1:  # Odd dimension
                    if symmetry == 'antisymmetric':
                        with raises(ConfigError, match='No unit-determinant antisymmetric matrix exists in odd dimensions'):
                            SquareMatrices(**args)
                        continue
                    elif symmetry == 'antihermitian':
                        with raises(ConfigError, match='No unit-determinant antihermitian matrix exists in odd dimensions'):
                            SquareMatrices(**args)
                        continue
            if det == 0 and symmetry == 'antisymmetric':
                if comp:
                    with raises(ConfigError, match='Unable to generate complex zero determinant antisymmetric matrices'):
                        SquareMatrices(**args)
                    continue
                if shape % 2 == 0:  # Even dimension
                    with raises(ConfigError, match='Unable to generate real zero determinant antisymmetric matrices in even dimensions'):
                        SquareMatrices(**args)
                    continue

            # Matrix exists, so let's test
            matrices = SquareMatrices(**args)
            if symmetry in ('hermitian', 'antihermitian'):
                comp = True
            m = matrices.gen_sample()

            # MathArray
            assert isinstance(m, MathArray)

            # Shape
            assert m.shape == (shape, shape)

            # Norm
            if det != 1:
                computed_norm = np.linalg.norm(m)
                assert norm[0] <= computed_norm or abs(computed_norm - norm[0]) < 1e-12
                assert computed_norm <= norm[1] or abs(computed_norm - norm[1]) < 1e-12

            # Complex
            if not comp:
                assert np.array_equal(np.conj(m), m)

            # Trace
            if traceless:
                assert within_tolerance(m.trace(), 0, 5e-13)

            # Determinant
            if det == 0:
                assert within_tolerance(np.abs(np.linalg.det(m)), 0, 1e-12)
            elif det == 1:
                assert within_tolerance(np.abs(np.linalg.det(m)), 1, 1e-12)

            # Symmetries
            if symmetry == 'diagonal':
                assert np.array_equal(np.diag(np.diag(m)), m)
            elif symmetry == 'symmetric':
                assert np.array_equal(m, m.T)
            elif symmetry == 'antisymmetric':
                assert np.array_equal(m, -m.T)
            elif symmetry == 'hermitian':
                assert np.array_equal(m, np.conj(m.T))
            elif symmetry == 'antihermitian':
                assert np.array_equal(m, -np.conj(m.T))
