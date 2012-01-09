import asp.tree_grammar
import ast
import types


# grammar for functions that return either doubleint or one of the
# user-defined Obj types
asp.tree_grammar.parse('''

UnaryFunction(input=Identifier, body=Expr)

Expr =  Constant
          | Identifier 
          | BinaryOp
          | BoolConstant
          | IfExp
          | Attribute
          | FunctionReturn
          | Compare


Identifier(name=types.StringType)





Compare(left=Expr, op=(ast.Eq | ast.NotEq | ast.Lt | ast.LtE | ast.Gt | ast.GtE), right=Expr)


Constant(value = types.IntType | types.FloatType)

BinaryOp(left=Expr, op=(ast.Add | ast.Sub), right=Expr)

BoolConstant(value = types.BooleanType)


IfExp(test=(Compare|Attribute|Identifier|BoolConstant), body=Expr, orelse=Expr)



# this if for a.b
Attribute(value=Identifier, attr=Identifier)

# a return here is different than in the predicate classes.  Here, the return must have a 
# constructor, so it looks like "return FooClass(value)"
FunctionReturn(ret_type = Identifier, value = Expr*)
''', globals())