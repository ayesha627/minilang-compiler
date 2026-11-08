"""
AST Node Definitions for MiniLang++
"""

from enum import Enum

class Type(Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    VOID = "void"
    ERROR = "error"

class Operator(Enum):
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    AND = "&&"
    OR = "||"
    NOT = "!"
    NEG = "neg"

class ASTNode:
    def __init__(self, line=0, column=0):
        self.line = line
        self.column = column
        self.type = None

class Program(ASTNode):
    def __init__(self, declarations=None, line=0, column=0):
        super().__init__(line, column)
        self.declarations = declarations or []

class VarDecl(ASTNode):
    def __init__(self, var_type=Type.INT, name="", initializer=None,
                 is_array=False, array_size=None, line=0, column=0):
        super().__init__(line, column)
        self.var_type = var_type
        self.name = name
        self.initializer = initializer
        self.is_array = is_array
        self.array_size = array_size

class FuncDecl(ASTNode):
    def __init__(self, return_type=Type.VOID, name="", params=None, body=None, line=0, column=0):
        super().__init__(line, column)
        self.return_type = return_type
        self.name = name
        self.params = params or []
        self.body = body

class Param(ASTNode):
    def __init__(self, param_type=Type.INT, name="", line=0, column=0):
        super().__init__(line, column)
        self.param_type = param_type
        self.name = name

class Block(ASTNode):
    def __init__(self, statements=None, line=0, column=0):
        super().__init__(line, column)
        self.statements = statements or []

class Assignment(ASTNode):
    def __init__(self, target="", value=None, index=None, line=0, column=0):
        super().__init__(line, column)
        self.target = target
        self.value = value
        self.index = index

class IfStmt(ASTNode):
    def __init__(self, condition=None, then_block=None, else_block=None, line=0, column=0):
        super().__init__(line, column)
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

class WhileStmt(ASTNode):
    def __init__(self, condition=None, body=None, line=0, column=0):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

class ReturnStmt(ASTNode):
    def __init__(self, value=None, line=0, column=0):
        super().__init__(line, column)
        self.value = value

class BinaryExpr(ASTNode):
    def __init__(self, op=Operator.PLUS, left=None, right=None, line=0, column=0):
        super().__init__(line, column)
        self.op = op
        self.left = left
        self.right = right

class UnaryExpr(ASTNode):
    def __init__(self, op=Operator.NEG, operand=None, line=0, column=0):
        super().__init__(line, column)
        self.op = op
        self.operand = operand

class IntegerLiteral(ASTNode):
    def __init__(self, value=0, line=0, column=0):
        super().__init__(line, column)
        self.value = value
        self.type = Type.INT

class FloatLiteral(ASTNode):
    def __init__(self, value=0.0, line=0, column=0):
        super().__init__(line, column)
        self.value = value
        self.type = Type.FLOAT

class BoolLiteral(ASTNode):
    def __init__(self, value=False, line=0, column=0):
        super().__init__(line, column)
        self.value = value
        self.type = Type.BOOL

class Identifier(ASTNode):
    def __init__(self, name="", index=None, line=0, column=0):
        super().__init__(line, column)
        self.name = name
        self.index = index

class FuncCall(ASTNode):
    def __init__(self, name="", arguments=None, line=0, column=0):
        super().__init__(line, column)
        self.name = name
        self.arguments = arguments or []

class ExprStmt(ASTNode):
    def __init__(self, expression=None, line=0, column=0):
        super().__init__(line, column)
        self.expression = expression