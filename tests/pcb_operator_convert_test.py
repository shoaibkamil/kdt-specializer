import unittest2 as unittest
from pcb_operator_sm import * 
from pcb_operator_convert import *

def strip_whitespace(x):
    import re
    return (re.subn("\s", "", str(x)))[0]

class BasicConvertTests(unittest.TestCase):
    def test_basic(self):
        f = UnaryPredicate(input=Identifier(name="foo"),
                           body=Return(value=BoolConstant(True)))
        out = PcbOperatorConvert().convert(f)
        print out
        self.assertEqual(strip_whitespace(out),
                    strip_whitespace("""
template <class T>
bool call(T& foo)
{
  return true;
}
                    """))

    def test_with_if(self):
        f = UnaryPredicate(input=Identifier(name="foo"),
                           body=IfExp(test=BoolConstant(False),
                                      body=Return(value=BoolConstant(True)),
                                      orelse=Return(value=BoolConstant(False))))
        out = PcbOperatorConvert().convert(f)
        print out
        self.assertEqual(strip_whitespace(out),
                         strip_whitespace("""
template <class T>
bool call(T& foo)
{
  if (false)
    return true;
  else
    return false;
}
                    """))
                         

if __name__ == '__main__':
    unittest.main()