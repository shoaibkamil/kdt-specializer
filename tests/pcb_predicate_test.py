import unittest2 as unittest
from pcb_predicate_sm import * 
from pcb_operator_convert import *
from pcb_predicate import *
import kdt

def strip_whitespace(x):
    import re
    return (re.subn("\s", "", str(x)))[0]

class UnaryPredBasicCompileTests(unittest.TestCase):
    def test_basic(self):
        import re

        f = UnaryPredicate(input=Identifier(name="foo"),
                           body=BoolReturn(value=BoolConstant(True)))
        out = PcbOperatorConvert().convert(f)
        
        a = PcbUnaryPredicate(f)
        
        self.assertTrue(re.search("UnaryPredicateObj", str(type(a.get_predicate()))))


class UnaryPredFullExample(unittest.TestCase):
    # function to generate graph; copied from kdt examples/FilteredBFS.py
    def generate(self, scale=5):        # type 1 is twitter: small number of heavy nodes
        type1 = kdt.DiGraph.generateRMAT(scale, element=1.0, edgeFactor=7, delIsolated=False, initiator=[0.60, 0.19, 0.16, 0.05])
        type1.e.apply(lambda x: 1)
        # type 2 is email: fairly even
        type2 = kdt.DiGraph.generateRMAT(scale, element=1.0, edgeFactor=4, delIsolated=False, initiator=[0.20, 0.25, 0.25, 0.30])
        type2.e.apply(lambda x: 2)
        
        G = type1
        G.e = type1.e + type2.e
        return G

    def test_applying_filter(self):
        G = self.generate()
        print G.e._m_.__class__
        def f1(x):
            print "HAHA"
            return (x != 2)

#        G.e._m_.Prune(kdt.pcb.unaryObjPred(f1))
        
        # SEJITS code
        f = UnaryPredicate(input=Identifier(name="foo"),
                           body=BoolReturn(value=BoolConstant(False)))

        a = PcbUnaryPredicate(f)
        
        old = G.nedge()
        
        # pruning with this filter should do nothing.
        G.e._m_.Prune(a.get_predicate())

        self.assertEqual(old, G.nedge())

    def test_applying_nontrivial_filter(self):
        G = self.generate()
        Gcopy = G.copy()

        import ast
        f = UnaryPredicate(input=Identifier(name="boo"),
                           body=BoolReturn(value=Compare(left=Identifier(name="boo"),
                                                         op=ast.NotEq(),
                                                         right=Constant(value=2))))

        a = PcbUnaryPredicate(f)
        
        old = G.nedge()
        
        # first prune with SEJITS
        G.e._m_.Prune(a.get_predicate())
        print old, G.nedge()

        # now prune with "normal" kdt
        def f1(x):
            return (x != 2)

        Gcopy.e._m_.Prune(kdt.pcb.unaryObjPred(f1))

        # they better be the same
        self.assertEqual(G.nedge(), Gcopy.nedge())

        
if __name__ == '__main__':
    unittest.main()


