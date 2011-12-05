import asp.tree_grammar
import ast
import types

asp.tree_grammar.parse('''

UnaryPredicate(input=Identifier, body=BoolExpr)

BinaryPredicate(inputs=Identifier*, body=BoolExpr)
    check assert len(self.inputs)==2

Expr =  Constant
          | Identifier 
          | BinaryOp
          | BoolExpr


Identifier(name=types.StringType)


BoolExpr = BoolConstant
          | IfExp
          | Attribute
          | Return
          | Compare



Compare(left=Expr, op=(ast.Eq | ast.NotEq | ast.Lt | ast.LtE | ast.Gt | ast.GtE), right=Expr)


Constant(value = types.IntType | types.FloatType)

#BinaryOp(a=Expr, p=ast.Add, b=Expr)

BoolConstant(value = types.BooleanType)


IfExp(test=BoolExpr, body=BoolExpr, orelse=BoolExpr)



# this if for a.b
Attribute(value=Identifier, attr=Identifier)


Return(value = BoolExpr)




''', globals())