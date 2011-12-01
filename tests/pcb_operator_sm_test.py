import unittest2 as unittest

class ValidTests(unittest.TestCase):
    class UnaryBool(PcbUnaryBool):
        def apply(a):
            if a.something:
                return True
            else:
                return False

    class UnaryBool2(PcbUnaryBool):
        def apply(a):
            if a.something > 1.0:
                return False
            return True

    class UnaryBoolWithInit(PcbUnaryBool):
        def __init__(self, val):
            self.val = val
        def apply(a):
            if a.something == self.val:
                return True
            else:
                return False

if __name__ == '__main__':
    unittest.main()



# def my_SR_add(self, other):
#         return Obj1(self.weight + other.weight)
#         return self + other

# def my_SR_mul(A, B):
#         return max(A, B)

# sr = kdt.semiring(my_SR_mul, my_SR_add)

# myMat.SpGEMM(myOtherMat, sr)