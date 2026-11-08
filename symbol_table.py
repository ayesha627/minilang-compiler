"""
Scoped Symbol Table for MiniLang++
"""

from typing import Dict, List, Optional
from enum import Enum, auto

class SymbolType(Enum):
    VARIABLE = auto()
    FUNCTION = auto()
    PARAMETER = auto()

class Symbol:
    def __init__(self, name, symbol_type, data_type=None, scope_level=0, line=0, column=0,
                 is_initialized=False, is_array=False, array_size=None, param_types=None, return_type=None):
        self.name = name
        self.symbol_type = symbol_type
        self.data_type = data_type
        self.scope_level = scope_level
        self.line = line
        self.column = column
        self.is_initialized = is_initialized
        self.is_array = is_array
        self.array_size = array_size
        self.param_types = param_types or []
        self.return_type = return_type

    def __repr__(self):
        if self.symbol_type == SymbolType.FUNCTION:
            return f"Function '{self.name}' -> {self.return_type.name if self.return_type else 'None'} params={self.param_types}"
        return f"{'Var' if self.symbol_type == SymbolType.VARIABLE else 'Param'} '{self.name}': {self.data_type.name if self.data_type else 'None'} {'[init]' if self.is_initialized else '[uninit]'} level={self.scope_level}"

class SymbolTable:
    def __init__(self, name="global", parent=None):
        self.name = name
        self.parent = parent
        self.symbols = {}
        self.children = []
        self.scope_level = 0 if parent is None else parent.scope_level + 1

    def define(self, symbol):
        if symbol.name in self.symbols:
            return False
        self.symbols[symbol.name] = symbol
        return True

    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name):
        return self.symbols.get(name)

    def create_child(self, name):
        child = SymbolTable(name, self)
        self.children.append(child)
        return child

    def __repr__(self):
        indent = "  " * self.scope_level
        result = f"{indent}Scope '{self.name}' (level {self.scope_level}):\n"
        for sym in self.symbols.values():
            result += f"{indent}  {sym}\n"
        for child in self.children:
            result += str(child)
        return result

class SymbolTableManager:
    def __init__(self):
        self.global_scope = SymbolTable("global")
        self.current_scope = self.global_scope
        self.scope_stack = [self.global_scope]
        self.all_tables = [self.global_scope]

    def enter_scope(self, name):
        new_scope = self.current_scope.create_child(name)
        self.current_scope = new_scope
        self.scope_stack.append(new_scope)
        self.all_tables.append(new_scope)

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]

    def define(self, symbol):
        return self.current_scope.define(symbol)

    def lookup(self, name):
        return self.current_scope.lookup(name)

    def lookup_local(self, name):
        return self.current_scope.lookup_local(name)

    def get_current_scope_name(self):
        return self.current_scope.name

    def get_current_scope_level(self):
        return self.current_scope.scope_level

    def print_all_scopes(self):
        print("\n" + "=" * 60)
        print("SYMBOL TABLES")
        print("=" * 60)
        print(str(self.global_scope))
        print("=" * 60)