import unittest2 as unittest
from pcb_operator import *


class ProcessASTTests(unittest.TestCase):
    def test_unaryfunction_conversion(self):
        def test_op(self, x):
            return x

        import inspect, ast
        t = ast.parse(inspect.getsource(test_op).lstrip())
        sm = PcbOperator.ProcessAST(None).visit(t)

        self.assertEqual(type(sm.body[0]), PcbOperator.UnaryFunctionNode)

    def test_binaryfunction_conversion(self):
        def test_binop(self, x, y):
            return x+y
        import inspect, ast
        t = ast.parse(inspect.getsource(test_binop).lstrip())
        sm = PcbOperator.ProcessAST(Operator("test_binop", assoc=True, comm=True)).visit(t)

        self.assertEqual(type(sm.body[0]), PcbOperator.BinaryFunctionNode)


class FullUnitaryTests(unittest.TestCase):

    def test_unary_function(self):
        class MyOperator(PcbOperator):
            def invert(self, x):
                return -x
        ops = MyOperator([Operator("invert")])

        import re
        self.assertIn("Swig Object of type 'op::UnaryFunction *'", str(ops.mod.invert()))

        self.assertIn("Swig Object of type 'op::UnaryFunction *'", str(ops.invert()))

    def test_applying_unary_function(self):
        class MyOperator(PcbOperator):
            def invert(self, x):
                return -x
        ops = MyOperator([Operator("invert")])

        import kdt.pyCombBLAS as pcb
        d = pcb.pyDenseParVec.range(10, -5)
        d.printall()
        d.Apply(ops.invert())

        self.assertEqual(d[0], 5)

    def test_binary_function(self):
        class MyOperator(PcbOperator):
            def test_binop(self, x, y):
                return x + y

        ops = MyOperator([Operator("test_binop", comm=True, assoc=True)])

        import re
        self.assertIn("Swig Object of type 'op::BinaryFunction *'", str(ops.test_binop()))

    def test_applying_binary_function(self):
        class MyOperator(PcbOperator):
            def test_binop(self, x, y):
                return x + y

        ops = MyOperator([Operator("test_binop", comm=True, assoc=True)])

        import kdt.pyCombBLAS as pcb
        d = pcb.pyDenseParVec(10, -5)
        s = pcb.pyDenseParVec(10, 5)

        # this applies test_binop(x,y) for x,y in s,d
        s.EWiseApply(d, ops.test_binop())

        # test to see if the op worked
        for x in xrange(10):
            self.assertEqual(s[x], 0)


if __name__ == '__main__':
    unittest.main()
        
