"""
Main Driver for MiniLang++ Compiler
"""

import os
import sys
from ast_nodes import *
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from tac_generator import TACGenerator


def print_ast(node, indent=0):
    """Pretty print the AST"""
    prefix = "  " * indent
    if node is None:
        return

    if isinstance(node, Program):
        print(f"{prefix}Program")
        for decl in node.declarations:
            print_ast(decl, indent + 1)

    elif isinstance(node, VarDecl):
        init_str = f" = {print_ast_inline(node.initializer)}" if node.initializer else ""
        arr_str = f"[{node.array_size}]" if node.is_array else ""
        print(f"{prefix}VarDecl: {node.var_type.name} {node.name}{arr_str}{init_str}")

    elif isinstance(node, FuncDecl):
        params = ", ".join([f"{p.param_type.name} {p.name}" for p in node.params])
        print(f"{prefix}FuncDecl: {node.return_type.name} {node.name}({params})")
        print_ast(node.body, indent + 1)

    elif isinstance(node, Block):
        print(f"{prefix}Block")
        for stmt in node.statements:
            print_ast(stmt, indent + 1)

    elif isinstance(node, Param):
        # FIXED: was p.name, now node.name
        print(f"{prefix}Param: {node.param_type.name} {node.name}")

    elif isinstance(node, Assignment):
        index_str = f"[{print_ast_inline(node.index)}]" if node.index else ""
        print(f"{prefix}Assignment: {node.target}{index_str} = {print_ast_inline(node.value)}")

    elif isinstance(node, IfStmt):
        print(f"{prefix}If")
        print(f"{prefix}  Condition: {print_ast_inline(node.condition)}")
        print_ast(node.then_block, indent + 1)
        if node.else_block:
            print(f"{prefix}  Else")
            print_ast(node.else_block, indent + 1)

    elif isinstance(node, WhileStmt):
        print(f"{prefix}While")
        print(f"{prefix}  Condition: {print_ast_inline(node.condition)}")
        print_ast(node.body, indent + 1)

    elif isinstance(node, ReturnStmt):
        val = print_ast_inline(node.value) if node.value else "void"
        print(f"{prefix}Return: {val}")

    elif isinstance(node, ExprStmt):
        print(f"{prefix}ExprStmt: {print_ast_inline(node.expression)}")

    elif isinstance(node, BinaryExpr):
        print(f"{prefix}BinaryExpr: {node.op.value}")
        print_ast(node.left, indent + 1)
        print_ast(node.right, indent + 1)

    elif isinstance(node, UnaryExpr):
        print(f"{prefix}UnaryExpr: {node.op.value}")
        print_ast(node.operand, indent + 1)

    elif isinstance(node, FuncCall):
        args = ", ".join([print_ast_inline(a) for a in node.arguments])
        print(f"{prefix}FuncCall: {node.name}({args})")

    elif isinstance(node, Identifier):
        index_str = f"[{print_ast_inline(node.index)}]" if node.index else ""
        print(f"{prefix}Identifier: {node.name}{index_str}")

    elif isinstance(node, IntegerLiteral):
        print(f"{prefix}IntegerLiteral: {node.value}")

    elif isinstance(node, FloatLiteral):
        print(f"{prefix}FloatLiteral: {node.value}")

    elif isinstance(node, BoolLiteral):
        print(f"{prefix}BoolLiteral: {node.value}")


def print_ast_inline(node):
    """Compact AST representation for inline printing"""
    if node is None:
        return "None"
    if isinstance(node, IntegerLiteral):
        return str(node.value)
    if isinstance(node, FloatLiteral):
        return str(node.value)
    if isinstance(node, BoolLiteral):
        return str(node.value)
    if isinstance(node, Identifier):
        idx = f"[{print_ast_inline(node.index)}]" if node.index else ""
        return f"{node.name}{idx}"
    if isinstance(node, FuncCall):
        args = ", ".join([print_ast_inline(a) for a in node.arguments])
        return f"{node.name}({args})"
    if isinstance(node, BinaryExpr):
        return f"({print_ast_inline(node.left)} {node.op.value} {print_ast_inline(node.right)})"
    if isinstance(node, UnaryExpr):
        return f"({node.op.value}{print_ast_inline(node.operand)})"
    return str(node)


def compile_source(source_code, generate_tac=True):
    """
    Main compilation pipeline
    """
    results = {
        "success": True,
        "tokens": [],
        "ast": None,
        "errors": [],
        "warnings": [],
        "tac": []
    }

    print("=" * 60)
    print("MINILANG++ COMPILER")
    print("=" * 60)

    # ========== PHASE 1: LEXICAL ANALYSIS ==========
    print("\n[PHASE 1] LEXICAL ANALYSIS")
    print("-" * 40)

    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    results["tokens"] = tokens

    lexer.print_tokens()

    if lexer.get_errors():
        print("\nLEXICAL ERRORS:")
        for error in lexer.get_errors():
            print(f"  X {error}")
            results["errors"].append(str(error))
        results["success"] = False

    # ========== PHASE 2: SYNTAX ANALYSIS ==========
    print("\n[PHASE 2] SYNTAX ANALYSIS")
    print("-" * 40)

    parser = Parser(tokens)
    ast = parser.parse()
    results["ast"] = ast

    if ast:
        print("\nPARSE TREE (AST):")
        print_ast(ast)
    else:
        print("Failed to parse due to errors.")
        results["success"] = False

    if parser.get_errors():
        print("\nSYNTAX ERRORS:")
        for error in parser.get_errors():
            print(f"  X {error}")
            results["errors"].append(str(error))
        results["success"] = False

    # Stop if parsing failed
    if ast is None:
        return results

    # ========== PHASE 3: SEMANTIC ANALYSIS ==========
    print("\n[PHASE 3] SEMANTIC ANALYSIS")
    print("-" * 40)

    analyzer = SemanticAnalyzer()
    semantic_ok = analyzer.analyze(ast)

    analyzer.symtab.print_all_scopes()

    if analyzer.get_errors():
        print("\nSEMANTIC ERRORS:")
        for error in analyzer.get_errors():
            print(f"  X {error}")
            results["errors"].append(str(error))
        results["success"] = False

    if analyzer.get_warnings():
        print("\nWARNINGS:")
        for warning in analyzer.get_warnings():
            print(f"  ! {warning}")
            results["warnings"].append(str(warning))

    # ========== PHASE 4: INTERMEDIATE CODE GENERATION ==========
    if generate_tac and semantic_ok:
        print("\n[PHASE 4] INTERMEDIATE CODE GENERATION")
        print("-" * 40)

        tac_gen = TACGenerator()
        tac = tac_gen.generate(ast)
        results["tac"] = tac

        tac_gen.print_tac()

    # ========== SUMMARY ==========
    print("\n" + "=" * 60)
    print("COMPILATION SUMMARY")
    print("=" * 60)
    print(f"Lexical Errors:   {len(lexer.get_errors())}")
    print(f"Syntax Errors:    {len(parser.get_errors())}")
    print(f"Semantic Errors:  {len(analyzer.get_errors())}")
    print(f"Warnings:         {len(analyzer.get_warnings())}")
    print(f"Overall Status:   {'SUCCESS' if results['success'] else 'FAILED'}")
    print("=" * 60)

    return results


def load_test_file(filename):
    """Load a test program from the test_programs folder"""
    possible_paths = [
        os.path.join("test_programs", filename),
        os.path.join(os.path.dirname(__file__), "test_programs", filename),
        os.path.join(os.getcwd(), "test_programs", filename),
    ]
    
    for filepath in possible_paths:
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
                return None
    
    print(f"Error: Could not find {filename} in any of these locations:")
    for p in possible_paths:
        print(f"  - {p}")
    return None


if __name__ == "__main__":
    print("=" * 60)
    print("MINILANG++ COMPILER - TEST SUITE")
    print("=" * 60)
    print("\nChoose a test program:")
    print("  1. test1_valid.txt   - Valid program")
    print("  2. test2_errors.txt  - Semantic Error Detection")
    print("  3. test3_arrays.txt  - Arrays")
    print("  4. test4_folding.txt - Constant Folding")
    print("  5. Custom input")

    choice = input("\nEnter choice (1-5): ").strip()

    test_files = {
        "1": "test1_valid.txt",
        "2": "test2_errors.txt",
        "3": "test3_arrays.txt",
        "4": "test4_folding.txt",
    }

    if choice in test_files:
        source = load_test_file(test_files[choice])
        if source is None:
            print("Exiting due to file error.")
            sys.exit(1)
    elif choice == "5":
        print("Enter your MiniLang++ code (empty line to finish):")
        lines = []
        while True:
            try:
                line = input()
                if line == "":
                    break
                lines.append(line)
            except EOFError:
                break
        source = "\n".join(lines)
    else:
        print("Invalid choice. Using test 1.")
        source = load_test_file("test1_valid.txt")
        if source is None:
            sys.exit(1)

    compile_source(source)