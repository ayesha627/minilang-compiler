# MiniLang++ Compiler

A Python-based compiler implementation for **MiniLang++**, a simple programming language. This project demonstrates the fundamental phases of compiler design, including lexical analysis, syntax analysis, semantic analysis, Abstract Syntax Tree (AST) construction, and intermediate code generation.

## Project Overview

MiniLang++ Compiler takes source code written in the MiniLang++ language and processes it through multiple compilation phases. It identifies tokens, checks syntax, validates semantic rules, constructs an Abstract Syntax Tree, and generates Three-Address Code (TAC) when the program passes semantic analysis.

## Features

- **Lexical Analysis:** Converts source code into tokens and identifies invalid characters and lexical errors.
- **Syntax Analysis:** Parses tokens according to the language grammar and detects syntax errors.
- **Abstract Syntax Tree (AST):** Builds a tree representation of the program structure.
- **Semantic Analysis:** Checks variable declarations, data types, function declarations, function calls, and other semantic rules.
- **Symbol Table Management:** Maintains symbol information and scopes.
- **Error Handling:** Reports lexical, syntax, and semantic errors with line and column information.
- **Intermediate Code Generation:** Generates Three-Address Code (TAC) for semantically valid programs.
- **Arrays:** Supports array declarations and indexed access.
- **Control Structures:** Supports conditional statements (`if-else`) and loops (`while`).
- **Functions:** Supports function declarations, parameters, function calls, and return statements.

## Technologies Used

- Python 3
- Object-Oriented Programming
- Compiler Design Concepts
- Data Structures

## Project Structure

```text
minilang_compiler/
│
├── main.py              # Main compiler pipeline and test runner
├── lexer.py             # Lexical analyzer
├── parser.py            # Syntax analyzer
├── ast_nodes.py         # Abstract Syntax Tree node definitions
├── semantic.py          # Semantic analysis
├── symbol_table.py      # Symbol table and scope management
├── tac_generator.py     # Three-Address Code generation
│
└── test_programs/
    ├── test1_valid.txt      # Valid MiniLang++ program
    ├── test2_errors.txt    # Semantic error detection tests
    ├── test3_arrays.txt    # Array operations
    └── test4_folding.txt   # Arithmetic and logical expression tests
```

## Supported Language Features

### Data Types
- `int`
- `float`
- `bool`
- `void`

### Operators
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Relational: `>`, `<`, `>=`, `<=`
- Equality: `==`, `!=`
- Logical: `&&`, `||`, `!`

### Statements and Constructs
- Variable declarations and assignments
- Array declarations and indexed access
- Function declarations and calls
- Conditional statements (`if`, `else`)
- While loops
- Return statements
- Integer, floating-point, and Boolean literals
- Single-line comments (`//`)

## How to Run

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/minilang-compiler.git
```

### 2. Navigate to the Project Directory

```bash
cd minilang-compiler
```

### 3. Run the Compiler

Make sure Python 3 is installed, then execute:

```bash
python main.py
```

### 4. Select a Test Program

The compiler provides an interactive menu:

| Option | Test Program | Description |
|---|---|---|
| 1 | test1_valid.txt | Tests a valid program |
| 2 | test2_errors.txt | Tests semantic error detection |
| 3 | test3_arrays.txt | Tests array functionality |
| 4 | test4_folding.txt | Tests arithmetic and logical expressions |
| 5 | Custom Input | Enter your own MiniLang++ code |

The compiler displays the results of the different compilation phases in the terminal.

## Compilation Workflow

```text
Source Code
    |
    v
Lexical Analysis
    |
    v
Syntax Analysis
    |
    v
Abstract Syntax Tree (AST)
    |
    v
Semantic Analysis
    |
    v
Three-Address Code Generation
    |
    v
Compilation Results
```

## Learning Objectives

This project was developed to understand and implement important concepts of compiler construction:

- Understanding the compiler pipeline.
- Implementing a lexical analyzer.
- Designing a parser.
- Constructing an Abstract Syntax Tree.
- Performing semantic checks.
- Managing symbol tables and scopes.
- Generating intermediate representations using Three-Address Code.
- Detecting and reporting compilation errors.

## Author

**Ayesha Imran**

Computer Science Student

## License

This project is intended for educational and learning purposes.
