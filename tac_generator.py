"""
Three-Address Code Generator for MiniLang++
"""

from typing import List
from ast_nodes import *

class TACInstruction:
    def __init__(self, op, arg1=None, arg2=None, result=None):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __repr__(self):
        if self.op in ("LABEL", "PARAM", "RETURN", "GOTO", "CALL", "ARG"):
            if self.arg2:
                return f"{self.op} {self.arg1}, {self.arg2}"
            return f"{self.op} {self.arg1}"
        if self.op in ("IF_FALSE", "IF_TRUE"):
            return f"IF {self.arg1} {self.op} GOTO {self.result}"
        if self.arg2 is None:
            return f"{self.result} = {self.op} {self.arg1}"
        return f"{self.result} = {self.arg1} {self.op} {self.arg2}"

class TACGenerator:
    def __init__(self):
        self.instructions = []
        self.temp_count = 0
        self.label_count = 0

    def _new_temp(self):
        self.temp_count += 1
        return f"t{self.temp_count}"

    def _new_label(self):
        self.label_count += 1
        return f"L{self.label_count}"

    def generate(self, ast):
        if ast is None:
            return []

        for decl in ast.declarations:
            if isinstance(decl, FuncDecl):
                self._generate_func_decl(decl)
            elif isinstance(decl, VarDecl):
                self._generate_global_var(decl)

        return self.instructions

    def _generate_global_var(self, node):
        if node.initializer:
            temp = self._generate_expression(node.initializer)
            self.instructions.append(TACInstruction("ASSIGN", temp, None, node.name))

    def _generate_func_decl(self, node):
        self.instructions.append(TACInstruction("LABEL", node.name))

        for param in node.params:
            self.instructions.append(TACInstruction("PARAM", param.name))

        self._generate_block(node.body)

        if node.return_type == Type.VOID:
            self.instructions.append(TACInstruction("RETURN"))

    def _generate_block(self, node):
        for stmt in node.statements:
            self._generate_statement(stmt)

    def _generate_statement(self, node):
        if isinstance(node, VarDecl):
            self._generate_var_decl(node)
        elif isinstance(node, Assignment):
            self._generate_assignment(node)
        elif isinstance(node, IfStmt):
            self._generate_if_stmt(node)
        elif isinstance(node, WhileStmt):
            self._generate_while_stmt(node)
        elif isinstance(node, ReturnStmt):
            self._generate_return_stmt(node)
        elif isinstance(node, ExprStmt):
            self._generate_expression(node.expression)
        elif isinstance(node, Block):
            self._generate_block(node)

    def _generate_var_decl(self, node):
        if node.initializer:
            temp = self._generate_expression(node.initializer)
            self.instructions.append(TACInstruction("ASSIGN", temp, None, node.name))

    def _generate_assignment(self, node):
        value_temp = self._generate_expression(node.value)

        if node.index is not None:
            index_temp = self._generate_expression(node.index)
            addr_temp = self._new_temp()
            # FIXED: node.name → node.target
            self.instructions.append(TACInstruction("INDEX", node.target, index_temp, addr_temp))
            self.instructions.append(TACInstruction("STORE", value_temp, None, addr_temp))
        else:
            self.instructions.append(TACInstruction("ASSIGN", value_temp, None, node.target))

    def _generate_if_stmt(self, node):
        cond_temp = self._generate_expression(node.condition)
        else_label = self._new_label()
        end_label = self._new_label()

        self.instructions.append(TACInstruction("IF_FALSE", cond_temp, None, else_label))
        self._generate_block(node.then_block)
        self.instructions.append(TACInstruction("GOTO", end_label))
        self.instructions.append(TACInstruction("LABEL", else_label))

        if node.else_block:
            self._generate_block(node.else_block)

        self.instructions.append(TACInstruction("LABEL", end_label))

    def _generate_while_stmt(self, node):
        start_label = self._new_label()
        end_label = self._new_label()

        self.instructions.append(TACInstruction("LABEL", start_label))
        cond_temp = self._generate_expression(node.condition)
        self.instructions.append(TACInstruction("IF_FALSE", cond_temp, None, end_label))
        self._generate_block(node.body)
        self.instructions.append(TACInstruction("GOTO", start_label))
        self.instructions.append(TACInstruction("LABEL", end_label))

    def _generate_return_stmt(self, node):
        if node.value:
            temp = self._generate_expression(node.value)
            self.instructions.append(TACInstruction("RETURN", temp))
        else:
            self.instructions.append(TACInstruction("RETURN"))

    def _generate_expression(self, node):
        if isinstance(node, IntegerLiteral):
            return str(node.value)
        if isinstance(node, FloatLiteral):
            return str(node.value)
        if isinstance(node, BoolLiteral):
            return "1" if node.value else "0"
        if isinstance(node, Identifier):
            if node.index is not None:
                index_temp = self._generate_expression(node.index)
                result = self._new_temp()
                self.instructions.append(TACInstruction("LOAD", node.name, index_temp, result))
                return result
            return node.name
        if isinstance(node, FuncCall):
            arg_temps = []
            for arg in node.arguments:
                arg_temps.append(self._generate_expression(arg))
            for temp in arg_temps:
                self.instructions.append(TACInstruction("ARG", temp))
            result = self._new_temp()
            self.instructions.append(TACInstruction("CALL", node.name, str(len(arg_temps)), result))
            return result
        if isinstance(node, BinaryExpr):
            left = self._generate_expression(node.left)
            right = self._generate_expression(node.right)
            result = self._new_temp()

            op_map = {
                Operator.PLUS: "+", Operator.MINUS: "-", Operator.MULTIPLY: "*",
                Operator.DIVIDE: "/", Operator.MODULO: "%",
                Operator.GT: ">", Operator.LT: "<", Operator.GTE: ">=",
                Operator.LTE: "<=", Operator.EQ: "==", Operator.NEQ: "!=",
                Operator.AND: "&&", Operator.OR: "||",
            }

            tac_op = op_map.get(node.op, node.op.value)
            self.instructions.append(TACInstruction(tac_op, left, right, result))
            return result
        if isinstance(node, UnaryExpr):
            operand = self._generate_expression(node.operand)
            result = self._new_temp()
            if node.op == Operator.NEG:
                self.instructions.append(TACInstruction("NEG", operand, None, result))
            elif node.op == Operator.NOT:
                self.instructions.append(TACInstruction("NOT", operand, None, result))
            return result
        return "0"

    def print_tac(self):
        print("\n" + "=" * 60)
        print("THREE-ADDRESS CODE")
        print("=" * 60)
        for i, instr in enumerate(self.instructions, 1):
            print(f"{i:3}: {instr}")
        print("=" * 60)