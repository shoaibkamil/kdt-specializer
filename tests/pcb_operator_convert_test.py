import unittest2 as unittest
from pcb_predicate_sm import * 
from pcb_operator_convert import *

def strip_whitespace(x):
    import re
    return (re.subn("\s", "", str(x)))[0]

class UnaryPredBasicConvertTests(unittest.TestCase):
    def test_basic(self):
        f = UnaryPredicate(input=Identifier(name="foo"),
                           body=BoolReturn(value=BoolConstant(True)))
        out = PcbOperatorConvert().convert(f)
        print out
        self.assertEqual(strip_whitespace(out),
                    strip_whitespace("""
class MyUnaryPredicate: public UnaryPredicateObj {
public:
template <class T>
bool call(T& foo)
{
  return true;
}
};
                    """))

    def test_with_if(self):
        f = UnaryPredicate(input=Identifier(name="foo"),
                           body=IfExp(test=BoolConstant(False),
                                      body=BoolReturn(value=BoolConstant(True)),
                                      orelse=BoolReturn(value=BoolConstant(False))))
        out = PcbOperatorConvert().convert(f)
        print out
        self.assertEqual(strip_whitespace(out),
                         strip_whitespace("""
class MyUnaryPredicate: public UnaryPredicateObj {
public:
template <class T>
bool call(T& foo)
{
  if (false)
    return true;
  else
    return false;
}
};
                    """))
                         

class UnaryPredRealisticConvertTests(unittest.TestCase):
    def test_with_comparison(self):
        f = UnaryPredicate(input=Identifier(name="foo"),
                           body=IfExp(test=Compare(left=Attribute(value=Identifier("foo"), attr=Identifier("thing")),
                                                   op=ast.Eq(),
                                                   right=Constant(10)),
                                      body=BoolReturn(value=BoolConstant(True)),
                                      orelse=BoolReturn(value=BoolConstant(False))))
        out = PcbOperatorConvert().convert(f)
        print out
        self.assertEqual(strip_whitespace(out),
                         strip_whitespace("""
class MyUnaryPredicate: public UnaryPredicateObj {
public:
template <class T>
bool call(T& foo)
{
  if (foo.thing == 10)
    return true;
  else
    return false;
}
};
                    """))


    def test_with_binop(self):
        f = UnaryPredicate(input=Identifier(name="foo"),
                           body=IfExp(test=Compare(left=BinaryOp(left=Attribute(value=Identifier("foo"), attr=Identifier("thing")),
                                                                 op=ast.Add(),
                                                                 right=Constant(10)),
                                                   op=ast.Eq(),
                                                   right=Constant(10)),
                                      body=BoolReturn(value=BoolConstant(True)),
                                      orelse=BoolReturn(value=BoolConstant(False))))
        out = PcbOperatorConvert().convert(f)
        print out
        self.assertEqual(strip_whitespace(out),
                         strip_whitespace("""
class MyUnaryPredicate: public UnaryPredicateObj {
public:
template <class T>
bool call(T& foo)
{
  if ((foo.thing+10) == 10)
    return true;
  else
    return false;
}
};
                    """))


class BinaryPredBasicConvertTests(unittest.TestCase):
    def test_basic(self):
        f = BinaryPredicate(inputs=[Identifier(name="foo"), Identifier(name="bar")],
                           body=BoolReturn(value=BoolConstant(True)))
        out = PcbOperatorConvert().convert(f)
        print out
        self.assertEqual(strip_whitespace(out),
                    strip_whitespace("""
class MyBinaryPredicate: public BinaryPredicateObj {
public:
template <class T>
bool call(T& foo, T& bar)
{
  return true;
}
};
                    """))

    def test_with_if(self):
        f = BinaryPredicate(inputs=[Identifier(name="foo"), Identifier(name="bar")],
                           body=IfExp(test=BoolConstant(False),
                                      body=BoolReturn(value=BoolConstant(True)),
                                      orelse=BoolReturn(value=BoolConstant(False))))
        out = PcbOperatorConvert().convert(f)
        print out
        self.assertEqual(strip_whitespace(out),
                         strip_whitespace("""
class MyBinaryPredicate: public BinaryPredicateObj {
public:
template <class T>
bool call(T& foo, T& bar)
{
  if (false)
    return true;
  else
    return false;
}
};
                    """))


if __name__ == '__main__':
    unittest.main()