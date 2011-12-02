import asp.codegen.ast_tools as ast_tools
import asp.codegen.cpp_ast as cpp_ast

class CppAttribute(cpp_ast.Generable):
    def __init__(self, value, attr):
        self._fields = ["value", "attr"]
        self.value = value
        self.attr = attr
    
    def generate(self, with_semicolon=False):
        yield "%s.%s" % (self.value, self.attr)

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

        return cpp_ast.FunctionBody(cpp_ast.Template("class T", cpp_ast.FunctionDeclaration(cpp_ast.Value("bool", "call"),
                                                                [cpp_ast.Reference(cpp_ast.Value("T", "foo"))])),
                                    cpp_ast.Block(contents=[self.visit(node.body)]))

    def visit_Return(self, node):
        return cpp_ast.ReturnStatement(self.visit(node.value))

    def visit_BoolConstant(self, node):
        if node.value:
            return "true"
        else:
            return "false"

    def visit_Constant(self, node):
        if isinstance(node.value, int):
            return cpp_ast.CNumber(node.value)
        else:
            return cpp_ast.CName(node.value)
            

    def visit_IfExp(self, node):
        return cpp_ast.IfConv(self.visit(node.test), self.visit(node.body), else_=self.visit(node.orelse))

    def visit_Compare(self, node):
        import ast
        comparator_map = {ast.Eq:"==", ast.NotEq:"!=", ast.Lt:"<", ast.LtE:"<=", ast.Gt:">", ast.GtE:">="}
        return cpp_ast.Compare(self.visit(node.left), comparator_map[node.op.__class__], self.visit(node.right))

    def visit_Attribute(self, node):
        return CppAttribute(self.visit(node.value), self.visit(node.attr))

    def visit_Identifier(self, node):
        return cpp_ast.CName(node.name)