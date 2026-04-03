# AlgoFlow — Pseudocode-to-Animated-Algorithm Compiler

> An interactive educational compiler that transforms pseudocode into live algorithm animations,  
> visualizing every stage: Lexing → Parsing → AST → IR → Optimization → CFG

---

## What Is This?

AlgoFlow is a **compiler design project** built as a full-stack web application. It implements a
complete multi-stage compilation pipeline entirely from scratch (no parser generators), and pairs it
with a browser-based visualizer that lets students see *what the compiler is doing* at every stage,
alongside *what the algorithm is doing* at runtime.

```
Pseudocode  ──►  Lexer  ──►  Parser  ──►  AST  ──►  IR Gen  ──►  Optimizer  ──►  CFG
    source          tokens       AST         nodes       TAC        5 passes      basic blocks
                                                            │
                                                            ▼
                                                  React + D3 + Canvas Frontend
                                                  (animation · AST tree · IR diff · CFG graph)
```

---

## Architecture

```
algoflow/
├── backend/                        Python compiler + FastAPI REST server
│   ├── main.py                     FastAPI app: /api/compile, /api/simulate, /api/templates
│   ├── requirements.txt
│   ├── Dockerfile
│   │
│   └── compiler/
│       ├── pipeline.py             Master orchestrator — calls every stage in sequence
│       ├── simulator.py            Algorithm execution trace generator (11 algorithms)
│       │
│       ├── lexer/
│       │   ├── tokens.py           TokenType enum (50+ token types) + Token dataclass
│       │   └── lexer.py            Hand-written scanner: indent/dedent, operators, literals
│       │
│       ├── parser/
│       │   └── parser.py           Recursive-descent parser → typed AST
│       │                           Full precedence: assign→or→and→not→cmp→add→mul→unary→postfix
│       │
│       ├── ast_nodes/
│       │   └── nodes.py            20 typed AST node dataclasses with JSON serialisation
│       │
│       ├── ir/
│       │   ├── ir.py               IROpCode enum (30 ops) + IRInstruction + IRProgram
│       │   └── generator.py        AST → Three-Address Code lowering pass
│       │
│       ├── optimizer/
│       │   └── passes.py           5 classical passes + OptimizationPipeline orchestrator
│       │                           CF → CP → CSE → LICM → DCE (order chosen for max effect)
│       │
│       └── cfg/
│           └── cfg_builder.py      Basic block formation + edge construction + reachability
│
└── frontend/                       React 18 + Vite + D3.js + Zustand
    ├── index.html
    ├── vite.config.js
    ├── package.json
    ├── Dockerfile
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── styles/globals.css      CSS custom properties design system
        ├── lib/
        │   ├── store.js            Zustand global state (compiler result, sim state, playback)
        │   ├── api.js              fetch-based API client
        │   └── templates.js        12 built-in pseudocode templates
        └── components/
            ├── Header.jsx          Logo + pass toggles + compile button
            ├── LeftPanel.jsx       Editor + algorithm picker + input array
            ├── TabBar.jsx          6-tab view switcher
            ├── AnimationPanel.jsx  Canvas renderer (arrays, DP tables, graphs)
            ├── ASTPanel.jsx        D3 horizontal tree layout
            ├── IRPanel.jsx         Split before/after Three-Address Code view
            ├── CFGPanel.jsx        D3 block diagram with edge labels
            └── Panels.jsx          Optimizations · Metrics · PlayBar · StatusBar
```

---

## Compiler Pipeline — Stage by Stage

### Stage 1 — Lexical Analysis (`compiler/lexer/`)

Hand-written scanner. No regex, no generator. Reads source character by character.

**Handles:**
- Python-style significant indentation → emits `INDENT` / `DEDENT` tokens
- Multi-character operators: `==`, `!=`, `<=`, `>=`, `+=`, `-=`, `*=`, `/=`, `**`, `->`
- 20 keywords: `function`, `while`, `if`, `elif`, `else`, `for`, `in`, `return`, `break`, `continue`, `and`, `or`, `not`, `true`, `false`, `null`, `let`, `each`, `def`, `func`
- Integer and float literals
- String literals with escape sequences
- Comment stripping (`//` and `#`)
- Line/column tracking for error messages

**Output:** flat `List[Token]`

---

### Stage 2 — Parsing (`compiler/parser/parser.py`)

Recursive-descent parser. Implements the full operator-precedence grammar:

```
program      → top_level*
top_level    → function_decl | statement
function     → 'function' IDENT '(' params ')' ':' block
block        → INDENT statement+ DEDENT
statement    → return | if | while | for | break | continue | expr_or_assign
expr         → or → and → not → comparison → additive → multiplicative → unary → postfix → primary
postfix      → primary ( '(' args ')' | '[' expr ']' | '.' IDENT )*
primary      → INTEGER | FLOAT | BOOL | NULL | IDENT | '(' expr ')' | '[' elems ']'
```

**Output:** typed `Program` AST node (recursive)

---

### Stage 3 — Abstract Syntax Tree (`compiler/ast_nodes/nodes.py`)

20 strongly-typed dataclass node types. Every node carries `line`, `col` for error reporting and `to_dict()` for JSON serialisation to the frontend.

| Category | Nodes |
|----------|-------|
| Top-level | `Program`, `FunctionDecl` |
| Statements | `AssignStmt`, `ReturnStmt`, `IfStmt`, `WhileStmt`, `ForStmt`, `BreakStmt`, `ContinueStmt`, `ExprStmt` |
| Expressions | `BinaryExpr`, `UnaryExpr`, `CallExpr`, `IndexExpr`, `MemberExpr` |
| Literals | `Identifier`, `IntLiteral`, `FloatLiteral`, `BoolLiteral`, `NullLiteral`, `ArrayLiteral` |

---

### Stage 4 — IR Generation (`compiler/ir/`)

Lowers the AST to **Three-Address Code (TAC)** — the standard representation from the Dragon Book and *Engineering a Compiler*.

Each instruction: `result = op arg1, arg2`

**30-opcode instruction set:**
```
ASSIGN                          x = y
ADD / SUB / MUL / DIV / MOD    x = y op z
NEG / NOT                       x = op y
EQ / NE / LT / GT / LE / GE    x = y cmp z
AND / OR                        x = y logic z
LABEL                           L_0:
JUMP                            goto L_0
JUMP_IF / JUMP_UNLESS           if x goto L_0
PARAM / CALL                    param x ; t = call f, n
RETURN                          return x
LOAD_IDX / STORE_IDX            x = arr[i] ; arr[i] = x
ALLOC                           x = alloc n
FUNC_BEGIN / FUNC_END           // function boundaries
```

Fresh temporaries `%t0`, `%t1`, … and labels `while_cond_0`, `if_end_1`, … are generated per function. `break`/`continue` are patched after the containing loop body is emitted.

---

### Stage 5 — Optimization (`compiler/optimizer/passes.py`)

Five classical passes, each independently toggleable from the UI. Pipeline runs in optimal order: **CF → CP → CSE → LICM → DCE** so earlier passes feed later ones.

#### Constant Folding (CF)
Evaluates binary expressions with two constant operands at compile time.
```
BEFORE:  %t0 = 5 + 3        AFTER:  %t0 = 8
BEFORE:  %t1 = 10 * 0       AFTER:  %t1 = 0
```

#### Constant Propagation (CP)
Tracks variables assigned a single constant and substitutes at every use.
```
BEFORE:  x = 5              AFTER:  x = 5
         %t0 = x + 1                %t0 = 5 + 1   ← x replaced by 5
```

#### Common Subexpression Elimination (CSE)
Detects identical computations (same opcode + operands) and reuses the first result.
```
BEFORE:  %t0 = a + b        AFTER:  %t0 = a + b
         %t1 = a + b                %t1 = %t0     ← reuse, no recomputation
```

#### Loop Invariant Code Motion (LICM)
Identifies computations inside loops whose operands do not change across iterations and hoists them before the loop header.
```
BEFORE:  while_cond:        AFTER:  %t0 = n - 1   ← hoisted before loop
           %t0 = n - 1              while_cond:
           ...                        ...
```

#### Dead Code Elimination (DCE)
Iteratively marks instructions whose results are never used and removes them (fixed-point iteration).
```
BEFORE:  %t0 = 999 * 42    AFTER:  (removed — result never read)
         return 0                   return 0
```

**Change log:** Every pass returns a structured list of changes (type, index, before/after) which the frontend renders as diffs in the Optimizations panel.

---

### Stage 6 — Control Flow Graph (`compiler/cfg/cfg_builder.py`)

Builds a CFG from the (potentially optimized) IR using standard basic block formation:

1. **Find leaders:** function entry + every LABEL target + every instruction after a branch
2. **Form basic blocks:** leader to next leader
3. **Add edges:**
   - `JUMP` → unconditional edge to target
   - `JUMP_IF` → true edge to target, false edge to fall-through
   - `JUMP_UNLESS` → false edge to target, true edge to fall-through
   - `RETURN` → marks block as exit, no successors
4. **Mark unreachability:** BFS from entry; unreachable blocks/edges marked `dead`
5. **Compute predecessors:** reverse edges for each block

**Output:** `CFG` with `BasicBlock` nodes (id, label, display_lines, is_entry, is_exit, successors, predecessors) and `CFGEdge` objects (source, target, type).

---

## Supported Algorithms (Simulator)

| Algorithm | Category | Steps example (n=5) |
|-----------|----------|---------------------|
| Bubble Sort | Sorting | 24 steps |
| Selection Sort | Sorting | 15 steps |
| Insertion Sort | Sorting | 17 steps |
| Merge Sort | Sorting | 13 steps |
| Quick Sort | Sorting | 16 steps |
| Binary Search | Searching | 3–5 steps |
| Linear Search | Searching | 1–n steps |
| BFS | Graph | O(V+E) steps |
| DFS | Graph | O(V+E) steps |
| Fibonacci (DP) | Dynamic Programming | n steps |
| LCS | Dynamic Programming | m×n steps |
| 0/1 Knapsack | Dynamic Programming | n×W steps |

Each step carries: `action`, `description`, `array`/`dp_table`/`graph_state`, `highlights`, running `comparisons`/`swaps`/`accesses`, and `ir_index` for IR synchronisation.

---

## API Reference

### `POST /api/compile`
```json
// Request
{ "source": "function BubbleSort(arr, n):\n    ...", "passes": { "DCE": true, "CP": true, "CF": true, "CSE": true, "LICM": true } }

// Response
{
  "tokens":    [{ "type": "FUNCTION", "value": "function", "line": 1, "col": 1 }, ...],
  "ast":       { "node_type": "Program", "body": [...] },
  "ir_before": { "functions": [{ "name": "BubbleSort", "instructions": [...] }] },
  "ir_after":  [{ "function": "BubbleSort", "before": [...], "after": [...], "passes": { "CF": {...}, "DCE": {...} }, "stats": {...} }],
  "cfg":       [{ "function_name": "BubbleSort", "blocks": [...], "edges": [...] }],
  "stats":     { "ir_before_count": 39, "ir_after_count": 33, "reduction_pct": 15.4, "total_blocks": 11, "total_time_ms": 3.36 },
  "timings":   { "lexer": 0.12, "parser": 0.8, "ir_gen": 0.5, "optimizer": 1.2, "cfg": 0.7 },
  "errors":    []
}
```

### `POST /api/simulate`
```json
// Request
{ "algorithm": "bubble", "input_data": [64, 34, 25, 12, 22, 11, 90] }

// Response
{
  "steps": [
    { "step_number": 0, "action": "init", "description": "Start Bubble Sort  n=7", "array": [64,34,25,12,22,11,90], "highlights": [], "comparisons": 0, "swaps": 0, "accesses": 0 },
    { "step_number": 1, "action": "compare", "description": "Compare arr[0]=64 vs arr[1]=34", "array": [64,34,...], "highlights": [0,1], "comparisons": 1 },
    ...
  ],
  "metrics": { "comparisons": 15, "swaps": 8, "accesses": 30, "complexity": { "time": "O(n²)", "space": "O(1)" } }
}
```

### `GET /api/templates`
Returns all 12 built-in pseudocode templates with name, category, complexity.

### `GET /api/health`
Returns `{ "status": "ok", "version": "1.0.0" }`.

---

## Setup & Running

### Requirements
- Python 3.10+
- Node.js 18+

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# API docs at: http://localhost:8000/docs
```

### Frontend (dev)
```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

### Frontend (production — served by backend)
```bash
cd frontend && npm run build    # → frontend/dist/
cd ../backend && uvicorn main:app --port 8000
# Everything served at http://localhost:8000
```

### Run Tests
```bash
cd backend
pytest tests/ -v
```

### Docker (both services)
```bash
docker-compose up --build
```

### Quick Setup Script
```bash
chmod +x setup.sh && ./setup.sh
```

---

## Pseudocode Language

AlgoFlow accepts Python-like pseudocode. No strict syntax — the lexer is forgiving.

```python
function FunctionName(param1, param2):
    // or # comments are stripped by the lexer

    x = 5 + 3               // assignment
    arr[i] = arr[j]          // array write

    while condition:         // while loop
        if a > b:
            temp = a
            a = b
            b = temp
        elif a == b:
            break
        else:
            continue

    for each item in list:   // for-each
        result = result + item

    return result

// Operators: + - * / % // ** == != < > <= >= and or not += -= *= /=
// Literals:  42  3.14  true  false  null  [1, 2, 3]
```

---

## Design Decisions

**Hand-written lexer/parser instead of ANTLR/Tree-sitter:**  
Every line is readable and teachable. A generated parser hides the mechanics; this one exposes them. The architecture directly mirrors what ANTLR would produce, making it easy to compare.

**Three-Address Code instead of SSA:**  
TAC is the canonical representation in both *Compilers: Principles, Techniques, and Tools* (Dragon Book) and *Engineering a Compiler* (Cooper & Torczon). It is simpler to visualize and understand than SSA while still supporting all five classical passes.

**Separate `/compile` and `/simulate` endpoints:**  
Compilation is source-language-agnostic. Simulation is algorithm-specific (for rich animation). Separating them gives the best of both: a real compiler pipeline on any pseudocode, plus high-fidelity animation for known algorithms.

**Iterative DCE:**  
Dead Code Elimination runs to fixed point (repeated until no more eliminations). A single pass can miss chains of dead instructions where A is dead only because B (which uses A) is also dead.

**CF before CP, CSE before DCE:**  
Running Constant Folding first turns variable-dependent expressions into constants, which CP can then propagate. CSE runs before DCE so that the eliminated duplicate expressions count toward DCE's dead set.

---

## Test Coverage

```
backend/tests/test_compiler.py

TestLexer           8 tests   integers, keywords, operators, identifiers, comments, INDENT/DEDENT, floats, EOF
TestParser          7 tests   functions, while, if/else, binary expr, index expr, nested calls, return
TestIRGenerator     7 tests   FUNC_BEGIN/END, ASSIGN, ADD, WHILE→labels+jumps, IF→JUMP_UNLESS, LOAD_IDX, multi-func
TestConstantFolding 4 tests   addition, multiplication, no-fold-variables, subtraction
TestConstantProp    2 tests   propagates const, does not propagate non-const
TestDCE             2 tests   eliminates unused temp, keeps used values
TestCSE             1 test    eliminates duplicate expression
TestOptPipeline     3 tests   runs all passes, respects disabled passes, stats present
TestCFGBuilder      4 tests   entry block, exit block, while→back edge, if→branches
TestFullPipeline    5 tests   bubble sort compiles, optimization reduces IR, no errors, timings, stats
TestSimulator       8 tests   bubble/merge/quick sort, binary search, fibonacci, bfs, metrics
```

---

## License

MIT — AlgoFlow Compiler Design Project
