from pcb_function_sm import *
import unittest2 as unittest
from pcb_operator_convert import *

def strip_whitespace(x):
    import re
    return (re.subn("\s", "", str(x)))[0]


class UnaryFunctionBasicConvertTests(unittest.TestCase):

    def test_basic(self):
        f = UnaryFunction(input=Identifier(name="foo"),
                          body=FunctionReturn(ret_type=Identifier("SomeClass"),
                                              value=[]))
        out = PcbOperatorConvert().convert(f)
        print out
        self.assertEqual(strip_whitespace(out),
                         strip_whitespace("""
class MyUnaryFunction: public UnaryFunctionObj {
public:
template <class T>
T call(T& foo)
{
  return ((T)*(new SomeClass));
}                                          
};
                                          """))

if __name__ == '__main__':
    unittest.main()