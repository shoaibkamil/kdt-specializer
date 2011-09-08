#include "test.h"
#include "pyOperations.h"
#include "boost/python.hpp"
#include "swigpyrun.h"

namespace op {

  
  template <typename T>
  struct test_op_s : public ConcreteUnaryFunction<T>
  {
    T operator()(const T& x)
      const
    {
      return (x<0) ? -static_cast<doubleint>(x) : x;
    }
  } ;
  
  PyObject* test_op()
  {
    
    swig_module_info* module = SWIG_Python_GetModule();
    char query[] = "UnaryFunction";
    swig_type_info* ty = SWIG_TypeQueryModule(module, module, "op::UnaryFunction *");

    UnaryFunction retf = UnaryFunction(new test_op_s<doubleint>());
    
    PyObject* ret_obj = SWIG_NewPointerObj((void*)(&retf), ty, 0);

    return ret_obj;

  }
}



BOOST_PYTHON_MODULE(module)
{
  using namespace boost::python;
  def("test_op", op::test_op);

}
