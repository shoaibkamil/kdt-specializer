import asp.codegen.ast_tools as ast_tools
import asp.codegen.cpp_ast as cpp_ast

class PcbOperatorConvert(ast_tools.NodeTransformer):
    """
    This class is used to convert from a semantic model (expressed in terms of nodes in pcb_operator_sm)
    to a C++ AST that can then be further transformed or directly generated.
    """

    def convert(self, sm):
        """
        Entry point.  Call this on the semantic model.  Returns the C++ AST.
        """
        return self.visit(sm)


    def visit_UnaryPredicate(self, node):
        #FIXME: this should actually have const in the signature for the input, but doesn't look like CodePy
        # supports this properly
        return cpp_ast.FunctionBody(cpp_ast.FunctionDeclaration(cpp_ast.Value("bool", "call"),
                                                                [cpp_ast.Reference(cpp_ast.Value("T", "foo"))]),
                                    cpp_ast.Block(contents=[self.visit(node.body)]))

    def visit_Return(self, node):
        return cpp_ast.ReturnStatement(self.visit(node.value))

    def visit_BoolConstant(self, node):
        if node.value:
            return "true"
        else:
            return "false"