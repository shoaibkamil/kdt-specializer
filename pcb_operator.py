import inspect
import asp.codegen.python_ast as ast
import asp.codegen.cpp_ast as cpp_ast
import asp.codegen.ast_tools as ast_tools
import codepy.cgen
import asp.jit.asp_module as asp_module
from collections import namedtuple


class Template(cpp_ast.Template):
    def generate(self, with_semicolon=True):
        return super(Template, self).generate(with_semicolon)

class Line(cpp_ast.Line):
    # should be rolled into asp's cpp_ast
    def __init__(self, text):
        self.text = text
        self._fields = ['text']
        super(Line, self).__init__(text=text)

    def generate(self, with_semicolon=False):
        return super(Line, self).generate()

class Namespace(cpp_ast.Generable):
    """
    A generable AST node representing a namespace.
    Accepts arguments
    'name', the namespace name, and
    'body', a cpp_ast.Block containing the body of the namespace.
    """
    
    def __init__(self, name, body):
        self.name = name
        self.body = body
        self._fields = ['name', 'body']

    def generate(self, with_semicolon=False):
        yield 'namespace %s' % self.name
        assert isinstance(self.body, cpp_ast.Block)
        for line in self.body.generate(with_semicolon):
            yield line

class ConstFunctionDeclaration(cpp_ast.FunctionDeclaration):
    """
    Simply subclasses cpp_ast.FunctionDeclaration to add make it constant.
    Implementation of this might be better moved into FunctionDeclaration.
    """
    def generate(self, with_semicolon=True):
        for item in super(ConstFunctionDeclaration, self).generate(with_semicolon):
            yield item
        yield ' const'
                
class New(cpp_ast.Generable):
    """
    Generable AST node for a statement allocating new memory.
    Accepts 'typename', name of associated type.
    """
    def __init__(self, typename):
        self.typename = typename
    def generate(self, with_semicolon=False):
        gen_str = 'new ' + str(self.typename)
        if with_semicolon:
            gen_str += ';'
            
        yield gen_str
        
class Operator(object):
    """
    Class to represent the data associated with an operator.
    Used a class because empty fields are nicer than with NamedTuple.
    """
    def __init__(self, name, assoc=None, comm=None, src=None, ast=None):
        self.name = name
        self.src = src
        self.ast = ast
        self.assoc = assoc
        self.comm = comm

class PcbOperator(object):
    def __init__(self, operators):
        # check for 'op' method
        self.operators = operators
        #temp_path = "/tmp/" #"/home/harper/Documents/Work/SEJITS/temp/"
        #makefile_path = "/vagrant/KDTSpecializer/kdt/pyCombBLAS"
        include_files = ["pyOperations.h", "swigpyrun.h"]
        self.mod = mod = asp_module.ASPModule(specializer="kdt")

        # add some include directories
        for x in include_files:
            self.mod.add_header(x)
        self.mod.backends["c++"].toolchain.cc = "mpicxx"
        self.mod.backends["c++"].toolchain.cflags = ["-g", "-fPIC", "-shared"]
        self.mod.add_library("pycombblas",
                             ["/vagrant/kdt-0.1/kdt/pyCombBLAS"],
                             library_dirs=["/vagrant/kdt-0.1/build/lib.linux-i686-2.6"],
                             libraries=["mpi_cxx"])
                               

        # the pyCombBLAS library must be imported in order for the SWIG typelookup to work
        import kdt.pyCombBLAS
        
        for operator in self.operators:
            try:
                dir(self).index(operator.name)
            except ValueError:
                raise Exception('No %s method defined.' % operator.name)

            operator.src = inspect.getsource(getattr(self, operator.name))
            operator.ast = ast.parse(operator.src.lstrip())
            phase2 = PcbOperator.ProcessAST(operator).visit(operator.ast)
            converted = PcbOperator.ConvertAST().visit(phase2)

            print "==="
            print converted
            
            print "==="

            self.mod.backends["c++"].module.add_to_module(converted.contents[0:-1])
            self.mod.add_function(operator.name, converted.contents[2].text)

            # now delete the method so the lookup goes through the Asp module
            delattr(self.__class__, operator.name)
            
    def __getattr__(self, name):
        """
        Override getting attributes to look them up in the Asp Module first.
        """

        if hasattr(self.mod, name):
            return getattr(self.mod, name)()
        else:
            return object.__getattribute__(self, name)

        
    class UnaryFunctionNode(ast.AST):
        def __init__(self, name, args, body):
            self.name = name
            self.args = args
            self.body = body
            self._fields = ['name', 'args', 'body']
            super(PcbOperator.UnaryFunctionNode, self).__init__()

    class BinaryFunctionNode(ast.AST):
        def __init__(self, name, args, body, assoc, comm):
            self.name = name
            self.args = args
            self.body = body
            self.assoc = assoc
            self.comm = comm
            self._fields = ['name', 'args', 'body']
            super(PcbOperator.BinaryFunctionNode, self).__init__()
        
    class ProcessAST(ast_tools.NodeTransformer):
        def __init__(self, operator):
            self.operator = operator
            super(PcbOperator.ProcessAST, self).__init__()
            
        def visit_Number(self, node):
            new_node = cpp_ast.FunctionCall("doubleint", [node])
            return new_node
        
        def visit_FunctionDef(self, node):
            print node.args.args[0].id

            # if the function is passed in using "self" as the first arg, remove it
            if node.args.args[0].id == "self":
                node.args.args = node.args.args[1:] 
            
            if len(node.args.args) == 1:
                new_node = PcbOperator.UnaryFunctionNode(node.name, node.args, node.body)
            elif len(node.args.args) == 2:
                new_node = PcbOperator.BinaryFunctionNode(node.name, node.args, node.body,
                                                          self.operator.assoc, self.operator.comm)
            else:
                return node
            return new_node
            
    class ConvertAST(ast_tools.ConvertAST):
        def visit_Num(self, node):
            """If we find a number, want to convert it to a doubleint for PCB."""
            print dir(node)
            return cpp_ast.FunctionCall("doubleint", [node.n])

        def visit_UnaryFunctionNode(self, node):

            # Create the new function that does the same thing as 'op'
            new_function_decl = ConstFunctionDeclaration(
                cpp_ast.Value("T", "operator()"),
                [cpp_ast.Value("const T&", node.args.args[0].id)])

            # Add all of the contends of the old function to the new
            new_function_contents = cpp_ast.Block([self.visit(subnode) for subnode in node.body])

            new_function_body = cpp_ast.FunctionBody(new_function_decl, new_function_contents)
            operator_struct = Template(
                "typename T",
                cpp_ast.Struct(node.name+"_s : public ConcreteUnaryFunction<T>", [new_function_body])
                )

            # Finally, generate a function for constructing one of these operators
            import asp.codegen.templating.template as template
            t = template.Template("""
            PyObject* ${func_name}()
            {
              swig_module_info* module = SWIG_Python_GetModule();

              swig_type_info* ty = SWIG_TypeQueryModule(module, module, "op::UnaryFunction *");

              UnaryFunction* retf = new UnaryFunction(new ${func_name}_s<doubleint>());
              
              PyObject* ret_obj = SWIG_NewPointerObj((void*)(retf), ty, SWIG_POINTER_OWN | 0);
              
              return ret_obj;
            }
            """)

            new_constructor_function = Line(t.render(func_name=node.name))

            # Block for the module contents.
            main_block = cpp_ast.Block()
            main_block.append(Line("using namespace op;"))
            main_block.append(operator_struct)
            main_block.append(new_constructor_function)

            return main_block

        def visit_BinaryFunctionNode(self, node):
            # Create the new function that does the same thing as 'op'
            new_function_decl = ConstFunctionDeclaration(
                cpp_ast.Value("T", "operator()"),
                [cpp_ast.Value("const T&", node.args.args[0].id),
                 cpp_ast.Value("const T&", node.args.args[1].id)])

            # Add all of the contends of the old function to the new
            new_function_contents = cpp_ast.Block([self.visit(subnode) for subnode in node.body])

            new_function_body = cpp_ast.FunctionBody(new_function_decl, new_function_contents)
            operator_struct = Template(
                "typename T",
                cpp_ast.Struct(node.name+"_s : public ConcreteBinaryFunction<T>", [new_function_body])
                )

            # Finally, generate a function for constructing one of these operators
            # new_constructor_decl = cpp_ast.FunctionDeclaration(
            #     cpp_ast.Value("BinaryFunction", node.name),
            #     [] )
            # new_constructor_body = cpp_ast.ReturnStatement(
            #     cpp_ast.FunctionCall("BinaryFunction", [
            #             New(node.name+"_s<doubleint>()"),
            #             str(node.assoc).lower(), str(node.comm).lower()])
            #     )
            # new_constructor_function = cpp_ast.FunctionBody(new_constructor_decl, cpp_ast.Block([new_constructor_body]))
            
            import asp.codegen.templating.template as template
            t = template.Template("""
            PyObject* ${func_name}()
            {
              swig_module_info* module = SWIG_Python_GetModule();

              swig_type_info* ty = SWIG_TypeQueryModule(module, module, "op::BinaryFunction *");

              BinaryFunction* retf = new BinaryFunction(new ${func_name}_s<doubleint>(), ${str(assoc).lower()}, ${str(comm).lower()});
              
              PyObject* ret_obj = SWIG_NewPointerObj((void*)(retf), ty, SWIG_POINTER_OWN | 0);
              
              return ret_obj;
              }
            """)

            new_constructor_function = Line(t.render(func_name=node.name, assoc=node.assoc, comm=node.comm))

            
            # Block for the module contents.
            main_block = cpp_ast.Block()
            main_block.append(Line("using namespace op;"))
            main_block.append(operator_struct)
            main_block.append(new_constructor_function)
            return main_block

        def visit_Name(self, node):
            # We need to statically convert any variables to doubleints.
            
            return cpp_ast.FunctionCall("static_cast<doubleint>", [cpp_ast.CName(node.id)])


    def explore_ast(self, node, depth):
        print '  '*depth, node
        for n in ast.iter_child_nodes(node):
            self.explore_ast(n, depth+1) 
