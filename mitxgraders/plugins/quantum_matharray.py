from mitxgraders.helpers.calc import MathArray

class QuantumMathArray(MathArray):

    @property
    def shape_name(self):
        ndim = self.ndim
        shape = self.shape

        if ndim == 0:
            return 'scalar'
        elif ndim == 1:
            return 'state vector'
        elif ndim == 2:
            if shape[0] == 1:
                return 'bra'
            elif shape[1] == 1:
                return 'ket'
            else:
                return 'operator'
        else:
            return 'tensor'

    @property
    def description(self):
        return self.shape_name
