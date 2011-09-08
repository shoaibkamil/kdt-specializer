import inspect
import asp.codegen.python_ast as ast
import asp.codegen.cpp_ast as cpp_ast
import asp.codegen.ast_tools as ast_tools
import codepy.cgen
import asp.jit.asp_module as asp_module
from collections import namedtuple



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
        


class PcbOperator(object):
    def __init__(self, operators):
        # check for 'op' method
        self.operators = operators
        temp_path = "/tmp/" #"/home/harper/Documents/Work/SEJITS/temp/"
        makefile_path = "/vagrant/KDTSpecializer/kdt/pyCombBLAS"
        include_files = ["/vagrant/KDTSpecializer/kdt/pyCombBLAS/pyOperations.h"]
        mod = CMakeModule(temp_path, makefile_path, namespace="op", include_files=include_files)
        
        for operator in self.operators:
            try:
                dir(self).index(operator.name)
            except ValueError:
                raise Exception('No %s method defined.' % operator.name)

            operator.src = inspect.getsource(getattr(self, operator.name))
            operator.ast = ast.parse(operator.src.lstrip())
            phase2 = PcbOperator.ProcessAST(operator).visit(operator.ast)
            converted = PcbOperator.ConvertAST().visit(phase2)
            mod.add_struct(converted.contents[0])
            mod.add_function(converted.contents[1])

        mod.compile()

        
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
            operator_struct = cpp_ast.Template(
                "typename T",
                cpp_ast.Struct(node.name+"_s : public ConcreteUnaryFunction<T>", [new_function_body])
                )

            # Finally, generate a function for constructing one of these operators
            new_constructor_decl = cpp_ast.FunctionDeclaration(
                cpp_ast.Value("UnaryFunction", node.name),
                [] )
            new_constructor_body = cpp_ast.ReturnStatement(
                cpp_ast.FunctionCall("UnaryFunction", [
                        New(node.name+"_s<doubleint>()")])
                )
            new_constructor_function = cpp_ast.FunctionBody(new_constructor_decl, cpp_ast.Block([new_constructor_body]))
            
            # Block for the module contents.
            main_block = cpp_ast.Block()
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
            operator_struct = cpp_ast.Template(
                "typename T",
                cpp_ast.Struct(node.name+"_s : public ConcreteBinaryFunction<T>", [new_function_body])
                )

            # Finally, generate a function for constructing one of these operators
            new_constructor_decl = cpp_ast.FunctionDeclaration(
                cpp_ast.Value("BinaryFunction", node.name),
                [] )
            new_constructor_body = cpp_ast.ReturnStatement(
                cpp_ast.FunctionCall("BinaryFunction", [
                        New(node.name+"_s<doubleint>()"),
                        str(node.assoc).lower(), str(node.comm).lower()])
                )
            new_constructor_function = cpp_ast.FunctionBody(new_constructor_decl, cpp_ast.Block([new_constructor_body]))
            
            # Block for the module contents.
            main_block = cpp_ast.Block()
            main_block.append(operator_struct)
            main_block.append(new_constructor_function)
            return main_block


    def explore_ast(self, node, depth):
        print '  '*depth, node
        for n in ast.iter_child_nodes(node):
            self.explore_ast(n, depth+1) 
