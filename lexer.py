"""
Lexical Analyzer for MiniLang++
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional

class TokenType(Enum):
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    VOID = "void"
    IF = "if"
    ELSE = "else"
    WHILE = "while"
    RETURN = "return"
    TRUE = "true"
    FALSE = "false"
    IDENTIFIER = "IDENTIFIER"
    INTEGER_LITERAL = "INTEGER_LITERAL"
    FLOAT_LITERAL = "FLOAT_LITERAL"
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    MODULO = "%"
    ASSIGN = "="
    GT = ">"
    LT = "<"
    GTE = ">="
    LTE = "<="
    EQ = "=="
    NEQ = "!="
    AND = "&&"
    OR = "||"
    NOT = "!"
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    SEMICOLON = ";"
    COMMA = ","
    EOF = "EOF"
    INVALID = "INVALID"

@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    column: int

class LexerError(Exception):
    def __init__(self, message, line, column):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Lexical Error at line {line}, column {column}: {message}")

class Lexer:
    KEYWORDS = {
        'int': TokenType.INT, 'float': TokenType.FLOAT, 'bool': TokenType.BOOL,
        'void': TokenType.VOID, 'if': TokenType.IF, 'else': TokenType.ELSE,
        'while': TokenType.WHILE, 'return': TokenType.RETURN,
        'true': TokenType.TRUE, 'false': TokenType.FALSE,
    }

    TWO_CHAR_OPS = {
        '>=': TokenType.GTE, '<=': TokenType.LTE, '==': TokenType.EQ,
        '!=': TokenType.NEQ, '&&': TokenType.AND, '||': TokenType.OR,
    }

    SINGLE_CHAR_TOKENS = {
        '+': TokenType.PLUS, '-': TokenType.MINUS, '*': TokenType.MULTIPLY,
        '/': TokenType.DIVIDE, '%': TokenType.MODULO, '=': TokenType.ASSIGN,
        '>': TokenType.GT, '<': TokenType.LT, '!': TokenType.NOT,
        '(': TokenType.LPAREN, ')': TokenType.RPAREN, '{': TokenType.LBRACE,
        '}': TokenType.RBRACE, '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
        ';': TokenType.SEMICOLON, ',': TokenType.COMMA,
    }

    def __init__(self, source: str):
        self.source = source
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.column = 1
        self.errors = []

    def _current_char(self):
        if self.pos >= len(self.source):
            return None
        return self.source[self.pos]

    def _peek_char(self, offset=1):
        peek_pos = self.pos + offset
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]

    def _advance(self):
        if self.pos < len(self.source) and self.source[self.pos] == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        self.pos += 1

    def _skip_whitespace(self):
        while self._current_char() is not None and self._current_char() in ' \t\n\r':
            self._advance()

    def _skip_comment(self):
        if self._current_char() == '/' and self._peek_char() == '/':
            while self._current_char() is not None and self._current_char() != '\n':
                self._advance()

    def _read_number(self):
        start_line = self.line
        start_col = self.column
        num_str = ""
        is_float = False

        while self._current_char() is not None and (
            self._current_char().isdigit() or 
            (self._current_char() == '.' and not is_float)
        ):
            if self._current_char() == '.':
                is_float = True
            num_str += self._current_char()
            self._advance()

        if is_float:
            return Token(TokenType.FLOAT_LITERAL, num_str, start_line, start_col)
        return Token(TokenType.INTEGER_LITERAL, num_str, start_line, start_col)

    def _read_identifier(self):
        start_line = self.line
        start_col = self.column
        ident = ""

        while (self._current_char() is not None and 
               (self._current_char().isalnum() or self._current_char() == '_')):
            ident += self._current_char()
            self._advance()

        token_type = self.KEYWORDS.get(ident, TokenType.IDENTIFIER)
        return Token(token_type, ident, start_line, start_col)

    def tokenize(self):
        while self._current_char() is not None:
            self._skip_whitespace()
            if self._current_char() is None:
                break

            if self._current_char() == '/' and self._peek_char() == '/':
                self._skip_comment()
                continue

            start_line = self.line
            start_col = self.column
            char = self._current_char()

            if char.isdigit():
                self.tokens.append(self._read_number())
                continue

            if char.isalpha() or char == '_':
                self.tokens.append(self._read_identifier())
                continue

            two_char = char + (self._peek_char() or '')
            if two_char in self.TWO_CHAR_OPS:
                self._advance()
                self._advance()
                self.tokens.append(Token(self.TWO_CHAR_OPS[two_char], two_char, start_line, start_col))
                continue

            if char in self.SINGLE_CHAR_TOKENS:
                self._advance()
                self.tokens.append(Token(self.SINGLE_CHAR_TOKENS[char], char, start_line, start_col))
                continue

            self.errors.append(LexerError(f"Invalid character: '{char}'", start_line, start_col))
            self.tokens.append(Token(TokenType.INVALID, char, start_line, start_col))
            self._advance()

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def get_errors(self):
        return self.errors

    def print_tokens(self):
        print("=" * 60)
        print("TOKENS")
        print("=" * 60)
        for token in self.tokens:
            print(f"{token.type.name:20} | {token.value:15} | Line {token.line:3}, Col {token.column:3}")
        print("=" * 60)