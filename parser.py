"""
Syntax Analyzer (Recursive Descent Parser) for MiniLang++
"""

from typing import List, Optional
from lexer import Token, TokenType
from ast_nodes import *

class ParseError(Exception):
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Syntax Error at line {line}, column {column}: {message}")

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    def _current_token(self):
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def _peek_token(self, offset=1):
        peek_pos = self.pos + offset
        if peek_pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[peek_pos]

    def _match(self, *expected_types):
        current = self._current_token()
        if current.type in expected_types:
            self.pos += 1
            return current
        return None

    def _expect(self, expected_type, error_msg=None):
        token = self._match(expected_type)
        if token is None:
            current = self._current_token()
            msg = error_msg or f"Expected {expected_type.name}, got {current.type.name}"
            err = ParseError(msg, current.line, current.column)
            self.errors.append(err)
            # Try to recover
            self._synchronize(expected_type)
            return Token(expected_type, "", current.line, current.column)
        return token

    def _synchronize(self, *sync_tokens):
        while (self._current_token().type not in sync_tokens and 
               self._current_token().type != TokenType.EOF):
            self.pos += 1

    def _is_type_token(self, token):
        return token.type in (TokenType.INT, TokenType.FLOAT, TokenType.BOOL, TokenType.VOID)

    def parse(self):
        try:
            program = self._parse_program()
            if self._current_token().type != TokenType.EOF:
                self.errors.append(ParseError("Unexpected tokens after program end",
                              self._current_token().line, self._current_token().column))
            return program
        except Exception as e:
            self.errors.append(ParseError(f"Fatal parse error: {str(e)}", 0, 0))
            return None

    def _parse_program(self):
        declarations = []
        while self._current_token().type != TokenType.EOF:
            decl = self._parse_declaration()
            if decl is not None:
                declarations.append(decl)
        return Program(declarations=declarations)

    def _parse_declaration(self):
        if not self._is_type_token(self._current_token()):
            self.errors.append(ParseError(f"Expected type declaration, got {self._current_token().type.name}",
                          self._current_token().line, self._current_token().column))
            self._synchronize(TokenType.INT, TokenType.FLOAT, TokenType.BOOL, TokenType.VOID)
            return None

        # Look ahead: if next is IDENTIFIER and then LPAREN, it's a function
        if (self._peek_token().type == TokenType.IDENTIFIER and 
            self._peek_token(2).type == TokenType.LPAREN):
            return self._parse_func_decl()
        else:
            return self._parse_var_decl()

    def _parse_type(self):
        token = self._current_token()
        if token.type == TokenType.INT:
            self._match(TokenType.INT)
            return Type.INT
        elif token.type == TokenType.FLOAT:
            self._match(TokenType.FLOAT)
            return Type.FLOAT
        elif token.type == TokenType.BOOL:
            self._match(TokenType.BOOL)
            return Type.BOOL
        elif token.type == TokenType.VOID:
            self._match(TokenType.VOID)
            return Type.VOID
        else:
            self.errors.append(ParseError(f"Expected type, got {token.type.name}", token.line, token.column))
            return Type.ERROR

    def _parse_var_decl(self):
        type_token = self._parse_type()
        name_token = self._expect(TokenType.IDENTIFIER)
        is_array = False
        array_size = None

        # Check for array declaration: int arr[5];
        if self._match(TokenType.LBRACKET):
            size_token = self._expect(TokenType.INTEGER_LITERAL)
            array_size = int(size_token.value)
            is_array = True
            self._expect(TokenType.RBRACKET)

        initializer = None
        if self._match(TokenType.ASSIGN):
            initializer = self._parse_expression()

        self._expect(TokenType.SEMICOLON)

        return VarDecl(
            var_type=type_token, name=name_token.value, initializer=initializer,
            is_array=is_array, array_size=array_size, line=name_token.line, column=name_token.column
        )

    def _parse_func_decl(self):
        return_type = self._parse_type()
        name_token = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.LPAREN)
        params = self._parse_param_list()
        self._expect(TokenType.RPAREN)
        body = self._parse_block()

        return FuncDecl(
            return_type=return_type, name=name_token.value, params=params, body=body,
            line=name_token.line, column=name_token.column
        )

    def _parse_param_list(self):
        params = []
        if self._current_token().type == TokenType.RPAREN:
            return params

        params.append(self._parse_param())
        while self._match(TokenType.COMMA):
            params.append(self._parse_param())
        return params

    def _parse_param(self):
        """Parse function parameter - supports arrays like int arr[5]"""
        param_type = self._parse_type()
        name_token = self._expect(TokenType.IDENTIFIER)
        
        # Check for array parameter: int arr[5]
        is_array = False
        array_size = None
        if self._match(TokenType.LBRACKET):
            size_token = self._expect(TokenType.INTEGER_LITERAL)
            array_size = int(size_token.value)
            is_array = True
            self._expect(TokenType.RBRACKET)
        
        param = Param(
            param_type=param_type, name=name_token.value, line=name_token.line, column=name_token.column
        )
        # Store array info on param for semantic analysis
        param.is_array = is_array
        param.array_size = array_size
        return param

    def _parse_block(self):
        lbrace = self._expect(TokenType.LBRACE)
        statements = []

        while self._current_token().type != TokenType.RBRACE:
            if self._current_token().type == TokenType.EOF:
                self.errors.append(ParseError("Unexpected EOF, expected '}'",
                              self._current_token().line, self._current_token().column))
                break
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)

        self._expect(TokenType.RBRACE)
        return Block(statements=statements, line=lbrace.line, column=lbrace.column)

    def _parse_statement(self):
        token = self._current_token()

        if self._is_type_token(token):
            return self._parse_var_decl()

        if token.type == TokenType.IF:
            return self._parse_if_stmt()

        if token.type == TokenType.WHILE:
            return self._parse_while_stmt()

        if token.type == TokenType.RETURN:
            return self._parse_return_stmt()

        if token.type == TokenType.IDENTIFIER:
            # Look ahead to determine assignment vs function call/expression
            next_tok = self._peek_token()
            if next_tok.type == TokenType.ASSIGN or next_tok.type == TokenType.LBRACKET:
                return self._parse_assignment()
            else:
                return self._parse_expr_stmt()

        self.errors.append(ParseError(f"Unexpected token: {token.type.name}", token.line, token.column))
        self._synchronize(TokenType.SEMICOLON, TokenType.RBRACE)
        return None

    def _parse_assignment(self):
        name_token = self._expect(TokenType.IDENTIFIER)
        index = None

        # Array index assignment: arr[i] = value;
        if self._match(TokenType.LBRACKET):
            index = self._parse_expression()
            self._expect(TokenType.RBRACKET)

        self._expect(TokenType.ASSIGN)
        value = self._parse_expression()
        self._expect(TokenType.SEMICOLON)

        return Assignment(
            target=name_token.value, value=value, index=index,
            line=name_token.line, column=name_token.column
        )

    def _parse_if_stmt(self):
        if_token = self._match(TokenType.IF)
        self._expect(TokenType.LPAREN)
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN)
        then_block = self._parse_block()

        else_block = None
        if self._match(TokenType.ELSE):
            else_block = self._parse_block()

        return IfStmt(
            condition=condition, then_block=then_block, else_block=else_block,
            line=if_token.line, column=if_token.column
        )

    def _parse_while_stmt(self):
        while_token = self._match(TokenType.WHILE)
        self._expect(TokenType.LPAREN)
        condition = self._parse_expression()
        self._expect(TokenType.RPAREN)
        body = self._parse_block()

        return WhileStmt(
            condition=condition, body=body, line=while_token.line, column=while_token.column
        )

    def _parse_return_stmt(self):
        return_token = self._match(TokenType.RETURN)
        value = None

        if self._current_token().type != TokenType.SEMICOLON:
            value = self._parse_expression()

        self._expect(TokenType.SEMICOLON)
        return ReturnStmt(value=value, line=return_token.line, column=return_token.column)

    def _parse_expr_stmt(self):
        expr = self._parse_expression()
        self._expect(TokenType.SEMICOLON)
        return ExprStmt(expression=expr, line=expr.line, column=expr.column)

    def _parse_expression(self):
        return self._parse_or_expr()

    def _parse_or_expr(self):
        left = self._parse_and_expr()
        while self._match(TokenType.OR):
            op = Operator.OR
            right = self._parse_and_expr()
            left = BinaryExpr(op, left, right, left.line, left.column)
        return left

    def _parse_and_expr(self):
        left = self._parse_eq_expr()
        while self._match(TokenType.AND):
            op = Operator.AND
            right = self._parse_eq_expr()
            left = BinaryExpr(op, left, right, left.line, left.column)
        return left

    def _parse_eq_expr(self):
        left = self._parse_rel_expr()
        while True:
            if self._match(TokenType.EQ):
                op = Operator.EQ
            elif self._match(TokenType.NEQ):
                op = Operator.NEQ
            else:
                break
            right = self._parse_rel_expr()
            left = BinaryExpr(op, left, right, left.line, left.column)
        return left

    def _parse_rel_expr(self):
        left = self._parse_add_expr()
        while True:
            if self._match(TokenType.GT):
                op = Operator.GT
            elif self._match(TokenType.LT):
                op = Operator.LT
            elif self._match(TokenType.GTE):
                op = Operator.GTE
            elif self._match(TokenType.LTE):
                op = Operator.LTE
            else:
                break
            right = self._parse_add_expr()
            left = BinaryExpr(op, left, right, left.line, left.column)
        return left

    def _parse_add_expr(self):
        left = self._parse_mul_expr()
        while True:
            if self._match(TokenType.PLUS):
                op = Operator.PLUS
            elif self._match(TokenType.MINUS):
                op = Operator.MINUS
            else:
                break
            right = self._parse_mul_expr()
            left = BinaryExpr(op, left, right, left.line, left.column)
        return left

    def _parse_mul_expr(self):
        left = self._parse_unary_expr()
        while True:
            if self._match(TokenType.MULTIPLY):
                op = Operator.MULTIPLY
            elif self._match(TokenType.DIVIDE):
                op = Operator.DIVIDE
            elif self._match(TokenType.MODULO):
                op = Operator.MODULO
            else:
                break
            right = self._parse_unary_expr()
            left = BinaryExpr(op, left, right, left.line, left.column)
        return left

    def _parse_unary_expr(self):
        if self._match(TokenType.MINUS):
            operand = self._parse_unary_expr()
            return UnaryExpr(Operator.NEG, operand, operand.line, operand.column)

        if self._match(TokenType.NOT):
            operand = self._parse_unary_expr()
            return UnaryExpr(Operator.NOT, operand, operand.line, operand.column)

        return self._parse_primary()

    def _parse_primary(self):
        token = self._current_token()

        if self._match(TokenType.INTEGER_LITERAL):
            return IntegerLiteral(int(token.value), token.line, token.column)

        if self._match(TokenType.FLOAT_LITERAL):
            return FloatLiteral(float(token.value), token.line, token.column)

        if self._match(TokenType.TRUE):
            return BoolLiteral(True, token.line, token.column)

        if self._match(TokenType.FALSE):
            return BoolLiteral(False, token.line, token.column)

        if token.type == TokenType.IDENTIFIER:
            self._match(TokenType.IDENTIFIER)

            # Function call
            if self._match(TokenType.LPAREN):
                args = self._parse_arg_list()
                self._expect(TokenType.RPAREN)
                return FuncCall(
                    name=token.value, arguments=args, line=token.line, column=token.column
                )

            # Array access or simple identifier
            index = None
            if self._match(TokenType.LBRACKET):
                index = self._parse_expression()
                self._expect(TokenType.RBRACKET)

            return Identifier(token.value, index, token.line, token.column)

        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._expect(TokenType.RPAREN)
            return expr

        self.errors.append(ParseError(f"Unexpected token in expression: {token.type.name}",
                                      token.line, token.column))
        return IntegerLiteral(0, token.line, token.column)

    def _parse_arg_list(self):
        args = []
        if self._current_token().type == TokenType.RPAREN:
            return args

        args.append(self._parse_expression())
        while self._match(TokenType.COMMA):
            args.append(self._parse_expression())
        return args

    def get_errors(self):
        return self.errors