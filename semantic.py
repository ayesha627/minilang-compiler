"""
Semantic Analyzer for MiniLang++
"""

from typing import List, Optional, Set
from ast_nodes import *
from symbol_table import SymbolTableManager, Symbol, SymbolType

class SemanticError:
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Semantic Error at line {self.line}, column {self.column}: {self.message}"

class SemanticAnalyzer:
    def __init__(self):
        self.symtab = SymbolTableManager()
        self.errors = []
        self.current_function = None
        self.warnings = []
        self.initialized_vars = set()

    def analyze(self, ast):
        if ast is None:
            self.errors.append(SemanticError("No AST to analyze", 0, 0))
            return False

        self._collect_functions(ast)
        self._analyze_program(ast)
        return len(self.errors) == 0

    def _collect_functions(self, program):
        for decl in program.declarations:
            if isinstance(decl, FuncDecl):
                param_types = []
                for p in decl.params:
                    param_types.append(p.param_type)
                symbol = Symbol(
                    name=decl.name, symbol_type=SymbolType.FUNCTION,
                    data_type=decl.return_type, scope_level=0,
                    line=decl.line, column=decl.column,
                    param_types=param_types, return_type=decl.return_type
                )
                if not self.symtab.define(symbol):
                    self.errors.append(SemanticError(f"Function '{decl.name}' redeclared", decl.line, decl.column))

    def _analyze_program(self, program):
        for decl in program.declarations:
            if isinstance(decl, VarDecl):
                self._analyze_var_decl(decl, is_global=True)
            elif isinstance(decl, FuncDecl):
                self._analyze_func_decl(decl)

    def _analyze_var_decl(self, node, is_global=False):
        if node.initializer is not None:
            init_type = self._analyze_expression(node.initializer)
            if init_type != Type.ERROR and init_type != node.var_type:
                if not (node.var_type == Type.FLOAT and init_type == Type.INT):
                    self.errors.append(SemanticError(
                        f"Type mismatch in initialization: cannot assign {init_type.name} to {node.var_type.name}",
                        node.line, node.column))
                else:
                    node.initializer.type = Type.FLOAT

        symbol = Symbol(
            name=node.name, symbol_type=SymbolType.VARIABLE,
            data_type=node.var_type, scope_level=self.symtab.get_current_scope_level(),
            line=node.line, column=node.column,
            is_initialized=node.initializer is not None,
            is_array=node.is_array, array_size=node.array_size
        )

        if not self.symtab.define(symbol):
            self.errors.append(SemanticError(f"Variable '{node.name}' redeclared in same scope", node.line, node.column))

        if node.initializer is not None:
            self.initialized_vars.add(node.name)

    def _analyze_func_decl(self, node):
        self.current_function = node
        self.symtab.enter_scope(f"func_{node.name}")

        for param in node.params:
            symbol = Symbol(
                name=param.name, symbol_type=SymbolType.PARAMETER,
                data_type=param.param_type, scope_level=self.symtab.get_current_scope_level(),
                line=param.line, column=param.column, is_initialized=True,
                is_array=getattr(param, 'is_array', False),
                array_size=getattr(param, 'array_size', None)
            )
            if not self.symtab.define(symbol):
                self.errors.append(SemanticError(f"Parameter '{param.name}' redeclared", param.line, param.column))
            self.initialized_vars.add(param.name)

        self._analyze_block(node.body)

        if node.return_type != Type.VOID and not self._has_return(node.body):
            self.errors.append(SemanticError(f"Function '{node.name}' may not return a value", node.line, node.column))

        self.symtab.exit_scope()
        self.current_function = None
        self.initialized_vars.clear()

    def _has_return(self, block):
        for stmt in block.statements:
            if isinstance(stmt, ReturnStmt):
                return True
            if isinstance(stmt, IfStmt):
                if stmt.else_block and self._has_return(stmt.then_block) and self._has_return(stmt.else_block):
                    return True
        return False

    def _analyze_block(self, node):
        for stmt in node.statements:
            self._analyze_statement(stmt)

    def _analyze_statement(self, node):
        if isinstance(node, VarDecl):
            self._analyze_var_decl(node)
        elif isinstance(node, Assignment):
            self._analyze_assignment(node)
        elif isinstance(node, IfStmt):
            self._analyze_if_stmt(node)
        elif isinstance(node, WhileStmt):
            self._analyze_while_stmt(node)
        elif isinstance(node, ReturnStmt):
            self._analyze_return_stmt(node)
        elif isinstance(node, ExprStmt):
            self._analyze_expression(node.expression)
        elif isinstance(node, Block):
            self.symtab.enter_scope("block")
            self._analyze_block(node)
            self.symtab.exit_scope()

    def _analyze_assignment(self, node):
        symbol = self.symtab.lookup(node.target)
        if symbol is None:
            self.errors.append(SemanticError(f"Undeclared identifier '{node.target}'", node.line, node.column))
            return Type.ERROR

        if symbol.symbol_type == SymbolType.FUNCTION:
            self.errors.append(SemanticError(f"Cannot assign to function '{node.target}'", node.line, node.column))
            return Type.ERROR

        value_type = self._analyze_expression(node.value)

        if node.index is not None:
            if not symbol.is_array:
                self.errors.append(SemanticError(f"'{node.target}' is not an array", node.line, node.column))
            else:
                index_type = self._analyze_expression(node.index)
                if index_type != Type.INT and index_type != Type.ERROR:
                    self.errors.append(SemanticError("Array index must be integer", node.index.line, node.index.column))

        if value_type != Type.ERROR and value_type != symbol.data_type:
            if not (symbol.data_type == Type.FLOAT and value_type == Type.INT):
                self.errors.append(SemanticError(
                    f"Type mismatch: cannot assign {value_type.name} to {symbol.data_type.name}",
                    node.line, node.column))
            else:
                node.value.type = Type.FLOAT

        symbol.is_initialized = True
        self.initialized_vars.add(node.target)

    def _analyze_if_stmt(self, node):
        cond_type = self._analyze_expression(node.condition)
        if cond_type != Type.BOOL and cond_type != Type.ERROR:
            self.errors.append(SemanticError("If condition must be boolean", node.condition.line, node.condition.column))

        self.symtab.enter_scope("if_then")
        self._analyze_block(node.then_block)
        self.symtab.exit_scope()

        if node.else_block:
            self.symtab.enter_scope("if_else")
            self._analyze_block(node.else_block)
            self.symtab.exit_scope()

    def _analyze_while_stmt(self, node):
        cond_type = self._analyze_expression(node.condition)
        if cond_type != Type.BOOL and cond_type != Type.ERROR:
            self.errors.append(SemanticError("While condition must be boolean", node.condition.line, node.condition.column))

        self.symtab.enter_scope("while")
        self._analyze_block(node.body)
        self.symtab.exit_scope()

    def _analyze_return_stmt(self, node):
        if self.current_function is None:
            self.errors.append(SemanticError("Return statement outside function", node.line, node.column))
            return

        if node.value is None:
            if self.current_function.return_type != Type.VOID:
                self.errors.append(SemanticError(
                    f"Function must return {self.current_function.return_type.name}", node.line, node.column))
            return

        return_type = self._analyze_expression(node.value)
        if return_type != Type.ERROR and return_type != self.current_function.return_type:
            if not (self.current_function.return_type == Type.FLOAT and return_type == Type.INT):
                self.errors.append(SemanticError(
                    f"Return type mismatch: expected {self.current_function.return_type.name}, got {return_type.name}",
                    node.line, node.column))

    def _analyze_expression(self, node):
        if isinstance(node, IntegerLiteral):
            node.type = Type.INT
            return Type.INT
        if isinstance(node, FloatLiteral):
            node.type = Type.FLOAT
            return Type.FLOAT
        if isinstance(node, BoolLiteral):
            node.type = Type.BOOL
            return Type.BOOL
        if isinstance(node, Identifier):
            return self._analyze_identifier(node)
        if isinstance(node, FuncCall):
            return self._analyze_func_call(node)
        if isinstance(node, BinaryExpr):
            return self._analyze_binary_expr(node)
        if isinstance(node, UnaryExpr):
            return self._analyze_unary_expr(node)
        return Type.ERROR

    def _analyze_identifier(self, node):
        symbol = self.symtab.lookup(node.name)
        if symbol is None:
            self.errors.append(SemanticError(f"Undeclared identifier '{node.name}'", node.line, node.column))
            return Type.ERROR

        if symbol.symbol_type == SymbolType.FUNCTION:
            self.errors.append(SemanticError(f"Function '{node.name}' used as variable", node.line, node.column))
            return Type.ERROR

        if not symbol.is_initialized and node.name not in self.initialized_vars:
            self.warnings.append(SemanticError(
                f"Variable '{node.name}' may be used before initialization", node.line, node.column))

        if node.index is not None:
            if not symbol.is_array:
                self.errors.append(SemanticError(f"'{node.name}' is not an array", node.line, node.column))
            else:
                index_type = self._analyze_expression(node.index)
                if index_type != Type.INT and index_type != Type.ERROR:
                    self.errors.append(SemanticError("Array index must be integer", node.index.line, node.index.column))
            return symbol.data_type

        node.type = symbol.data_type
        return symbol.data_type

    def _analyze_func_call(self, node):
        symbol = self.symtab.lookup(node.name)
        if symbol is None:
            self.errors.append(SemanticError(f"Undeclared function '{node.name}'", node.line, node.column))
            return Type.ERROR

        if symbol.symbol_type != SymbolType.FUNCTION:
            self.errors.append(SemanticError(f"'{node.name}' is not a function", node.line, node.column))
            return Type.ERROR

        if len(node.arguments) != len(symbol.param_types):
            self.errors.append(SemanticError(
                f"Function '{node.name}' expects {len(symbol.param_types)} arguments, got {len(node.arguments)}",
                node.line, node.column))
            return Type.ERROR

        for i, (arg, expected_type) in enumerate(zip(node.arguments, symbol.param_types)):
            arg_type = self._analyze_expression(arg)
            if arg_type != Type.ERROR and arg_type != expected_type:
                if not (expected_type == Type.FLOAT and arg_type == Type.INT):
                    self.errors.append(SemanticError(
                        f"Argument {i+1} type mismatch in call to '{node.name}': expected {expected_type.name}, got {arg_type.name}",
                        arg.line, arg.column))
                else:
                    arg.type = Type.FLOAT

        node.type = symbol.return_type
        return symbol.return_type

    def _analyze_binary_expr(self, node):
        left_type = self._analyze_expression(node.left)
        right_type = self._analyze_expression(node.right)

        if left_type == Type.ERROR or right_type == Type.ERROR:
            node.type = Type.ERROR
            return Type.ERROR

        if node.op in (Operator.PLUS, Operator.MINUS, Operator.MULTIPLY, Operator.DIVIDE, Operator.MODULO):
            if left_type not in (Type.INT, Type.FLOAT) or right_type not in (Type.INT, Type.FLOAT):
                self.errors.append(SemanticError(
                    f"Arithmetic operation requires numeric types, got {left_type.name} and {right_type.name}",
                    node.line, node.column))
                node.type = Type.ERROR
                return Type.ERROR

            if left_type == Type.FLOAT or right_type == Type.FLOAT:
                node.type = Type.FLOAT
                return Type.FLOAT
            node.type = Type.INT
            return Type.INT

        if node.op in (Operator.GT, Operator.LT, Operator.GTE, Operator.LTE):
            if left_type not in (Type.INT, Type.FLOAT) or right_type not in (Type.INT, Type.FLOAT):
                self.errors.append(SemanticError("Relational comparison requires numeric types", node.line, node.column))
                node.type = Type.ERROR
                return Type.ERROR
            node.type = Type.BOOL
            return Type.BOOL

        if node.op in (Operator.EQ, Operator.NEQ):
            if left_type != right_type:
                self.errors.append(SemanticError(f"Cannot compare {left_type.name} with {right_type.name}", node.line, node.column))
                node.type = Type.ERROR
                return Type.ERROR
            node.type = Type.BOOL
            return Type.BOOL

        if node.op in (Operator.AND, Operator.OR):
            if left_type != Type.BOOL or right_type != Type.BOOL:
                self.errors.append(SemanticError("Logical operation requires boolean types", node.line, node.column))
                node.type = Type.ERROR
                return Type.ERROR
            node.type = Type.BOOL
            return Type.BOOL

        node.type = Type.ERROR
        return Type.ERROR

    def _analyze_unary_expr(self, node):
        operand_type = self._analyze_expression(node.operand)

        if operand_type == Type.ERROR:
            node.type = Type.ERROR
            return Type.ERROR

        if node.op == Operator.NEG:
            if operand_type not in (Type.INT, Type.FLOAT):
                self.errors.append(SemanticError(f"Unary minus requires numeric type, got {operand_type.name}", node.line, node.column))
                node.type = Type.ERROR
                return Type.ERROR
            node.type = operand_type
            return operand_type

        if node.op == Operator.NOT:
            if operand_type != Type.BOOL:
                self.errors.append(SemanticError(f"Logical NOT requires boolean type, got {operand_type.name}", node.line, node.column))
                node.type = Type.ERROR
                return Type.ERROR
            node.type = Type.BOOL
            return Type.BOOL

        node.type = Type.ERROR
        return Type.ERROR

    def get_errors(self):
        return self.errors

    def get_warnings(self):
        return self.warnings