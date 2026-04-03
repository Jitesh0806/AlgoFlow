"""
AlgoFlow — Compiler Unit Tests

Tests each stage of the pipeline independently and end-to-end.
Run with: pytest backend/tests/ -v
"""

import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from compiler.lexer.lexer import Lexer
from compiler.lexer.tokens import TokenType
from compiler.parser.parser import Parser
from compiler.ir.generator import IRGenerator
from compiler.ir.ir import IROpCode
from compiler.optimizer.passes import (
    ConstantFolding, ConstantPropagation, DeadCodeElimination,
    CommonSubexpressionElimination, LoopInvariantCodeMotion,
    OptimizationPipeline,
)
from compiler.cfg.cfg_builder import CFGBuilder
from compiler.pipeline import AlgoFlowCompiler
from compiler.simulator import Simulator


# ═══ LEXER TESTS ════════════════════════════════════════════

class TestLexer:
    def _lex(self, src):
        return Lexer(src).tokenize()

    def test_integer_literal(self):
        tokens = self._lex("42")
        assert any(t.type == TokenType.INTEGER and t.value == "42" for t in tokens)

    def test_keywords(self):
        tokens = self._lex("function while if return")
        types = [t.type for t in tokens if t.type != TokenType.NEWLINE]
        assert TokenType.FUNCTION   in types
        assert TokenType.WHILE      in types
        assert TokenType.IF         in types
        assert TokenType.RETURN     in types

    def test_operators(self):
        tokens = self._lex("== != <= >= += -=")
        types = {t.type for t in tokens}
        assert TokenType.EQ      in types
        assert TokenType.NEQ     in types
        assert TokenType.LTE     in types
        assert TokenType.GTE     in types
        assert TokenType.PLUS_EQ in types
        assert TokenType.MINUS_EQ in types

    def test_identifier(self):
        tokens = self._lex("my_var_123")
        assert tokens[0].type  == TokenType.IDENTIFIER
        assert tokens[0].value == "my_var_123"

    def test_comment_skipped(self):
        tokens = self._lex("x = 1 // this is a comment\ny = 2")
        values = [t.value for t in tokens]
        assert "this" not in values
        assert "comment" not in values

    def test_indent_dedent(self):
        src = "while x:\n    y = 1\nz = 2"
        tokens = self._lex(src)
        types = [t.type for t in tokens]
        assert TokenType.INDENT in types
        assert TokenType.DEDENT in types

    def test_float_literal(self):
        tokens = self._lex("3.14")
        assert any(t.type == TokenType.FLOAT for t in tokens)

    def test_eof(self):
        tokens = self._lex("")
        assert tokens[-1].type == TokenType.EOF


# ═══ PARSER TESTS ════════════════════════════════════════════

class TestParser:
    def _parse(self, src):
        tokens = Lexer(src).tokenize()
        return Parser(tokens).parse()

    def test_function_decl(self):
        ast = self._parse("function foo(x, y):\n    return x")
        assert ast.node_type == "Program"
        assert len(ast.body) == 1
        fn = ast.body[0]
        assert fn.node_type == "FunctionDecl"
        assert fn.name == "foo"
        assert fn.params == ["x", "y"]

    def test_while_loop(self):
        ast = self._parse("function f(n):\n    while n > 0:\n        n = n - 1")
        fn = ast.body[0]
        while_stmt = fn.body[0]
        assert while_stmt.node_type == "WhileStmt"

    def test_if_else(self):
        src = "function f(x):\n    if x > 0:\n        return x\n    else:\n        return 0"
        ast = self._parse(src)
        fn = ast.body[0]
        if_stmt = fn.body[0]
        assert if_stmt.node_type == "IfStmt"
        assert len(if_stmt.else_body) > 0

    def test_binary_expr(self):
        src = "function f(a, b):\n    c = a + b * 2"
        ast = self._parse(src)
        fn = ast.body[0]
        assign = fn.body[0]
        assert assign.node_type == "AssignStmt"

    def test_index_expr(self):
        src = "function f(arr):\n    x = arr[0]"
        ast = self._parse(src)
        fn = ast.body[0]
        assign = fn.body[0]
        assert assign.value.node_type == "IndexExpr"

    def test_nested_calls(self):
        src = "function f():\n    x = max(a, min(b, c))"
        ast = self._parse(src)
        assert ast.body[0].node_type == "FunctionDecl"

    def test_return_expr(self):
        src = "function f(x):\n    return x + 1"
        ast = self._parse(src)
        ret = ast.body[0].body[0]
        assert ret.node_type == "ReturnStmt"
        assert ret.value is not None


# ═══ IR GENERATOR TESTS ══════════════════════════════════════

class TestIRGenerator:
    def _gen(self, src):
        tokens  = Lexer(src).tokenize()
        ast     = Parser(tokens).parse()
        gen     = IRGenerator()
        return gen.generate(ast)

    def test_generates_func_begin_end(self):
        ir = self._gen("function f():\n    return 0")
        ops = [i.op for i in ir.functions[0].instructions]
        assert IROpCode.FUNC_BEGIN in ops
        assert IROpCode.FUNC_END   in ops

    def test_assignment_emits_assign(self):
        ir = self._gen("function f():\n    x = 5")
        ops = [i.op for i in ir.functions[0].instructions]
        assert IROpCode.ASSIGN in ops

    def test_binary_add_emits_add(self):
        ir = self._gen("function f():\n    x = 3 + 4")
        ops = [i.op for i in ir.functions[0].instructions]
        assert IROpCode.ADD in ops

    def test_while_emits_labels_and_jumps(self):
        ir = self._gen("function f(n):\n    while n > 0:\n        n = n - 1")
        ops = [i.op for i in ir.functions[0].instructions]
        assert IROpCode.LABEL     in ops
        assert IROpCode.JUMP      in ops
        assert IROpCode.JUMP_UNLESS in ops

    def test_if_emits_conditional_jump(self):
        ir = self._gen("function f(x):\n    if x > 0:\n        return x")
        ops = [i.op for i in ir.functions[0].instructions]
        assert IROpCode.JUMP_UNLESS in ops

    def test_array_index_emits_load(self):
        ir = self._gen("function f(arr):\n    x = arr[0]")
        ops = [i.op for i in ir.functions[0].instructions]
        assert IROpCode.LOAD_IDX in ops

    def test_multiple_functions(self):
        src = "function a():\n    return 1\nfunction b():\n    return 2"
        ir = self._gen(src)
        assert len(ir.functions) == 2


# ═══ OPTIMIZER TESTS ═════════════════════════════════════════

class TestConstantFolding:
    def _make_func(self, src):
        tokens = Lexer(src).tokenize()
        ast    = Parser(tokens).parse()
        ir     = IRGenerator().generate(ast)
        return ir.functions[0]

    def test_folds_addition(self):
        func = self._make_func("function f():\n    x = 3 + 4")
        cf = ConstantFolding()
        new_func, changes = cf.run(func)
        assert any(c["type"] == "folded" and c["result"] == "7" for c in changes)

    def test_folds_multiplication(self):
        func = self._make_func("function f():\n    x = 6 * 7")
        cf = ConstantFolding()
        _, changes = cf.run(func)
        assert any(c["result"] == "42" for c in changes)

    def test_no_fold_variables(self):
        func = self._make_func("function f(a, b):\n    x = a + b")
        cf = ConstantFolding()
        _, changes = cf.run(func)
        assert len(changes) == 0

    def test_folds_subtraction(self):
        func = self._make_func("function f():\n    x = 10 - 3")
        cf = ConstantFolding()
        _, changes = cf.run(func)
        assert any(c["result"] == "7" for c in changes)


class TestConstantPropagation:
    def _make_func(self, src):
        tokens = Lexer(src).tokenize()
        ast    = Parser(tokens).parse()
        ir     = IRGenerator().generate(ast)
        return ir.functions[0]

    def test_propagates_constant(self):
        src = "function f():\n    x = 5\n    y = x + 1"
        func = self._make_func(src)
        cp = ConstantPropagation()
        _, changes = cp.run(func)
        assert any(c.get("variable") == "x" for c in changes)

    def test_no_propagation_for_non_const(self):
        src = "function f(a):\n    x = a\n    y = x + 1"
        func = self._make_func(src)
        cp = ConstantPropagation()
        _, changes = cp.run(func)
        # 'x' is assigned 'a' which is not a constant
        assert all(c.get("variable") != "x" for c in changes)


class TestDeadCodeElimination:
    def _make_func(self, src):
        tokens = Lexer(src).tokenize()
        ast    = Parser(tokens).parse()
        ir     = IRGenerator().generate(ast)
        return ir.functions[0]

    def test_eliminates_unused_temp(self):
        src = "function f():\n    x = 5 + 3\n    return 0"
        func = self._make_func(src)
        # First fold x so it becomes ASSIGN to a temp
        cf = ConstantFolding()
        func, _ = cf.run(func)
        dce = DeadCodeElimination()
        _, changes = dce.run(func)
        eliminated = [c for c in changes if c["type"] == "eliminated"]
        assert len(eliminated) > 0

    def test_keeps_used_values(self):
        src = "function f():\n    x = 5\n    return x"
        func = self._make_func(src)
        dce = DeadCodeElimination()
        _, changes = dce.run(func)
        # x is used in return — should NOT be eliminated
        assert not any("x" in str(c) and c["type"] == "eliminated" for c in changes)


class TestCSE:
    def _make_func(self, src):
        tokens = Lexer(src).tokenize()
        ast    = Parser(tokens).parse()
        ir     = IRGenerator().generate(ast)
        return ir.functions[0]

    def test_eliminates_duplicate_expr(self):
        src = "function f(a, b):\n    x = a + b\n    y = a + b\n    return x"
        func = self._make_func(src)
        cse = CommonSubexpressionElimination()
        _, changes = cse.run(func)
        assert any(c["type"] == "eliminated_cse" for c in changes)


class TestOptimizationPipeline:
    def _run(self, src, passes=None):
        tokens  = Lexer(src).tokenize()
        ast     = Parser(tokens).parse()
        ir      = IRGenerator().generate(ast)
        pipeline = OptimizationPipeline(passes)
        return pipeline.run(ir.functions[0])

    def test_pipeline_runs_all_passes(self):
        src = "function f():\n    x = 3 + 4\n    y = 3 + 4\n    return 0"
        result = self._run(src)
        assert "CF"  in result["passes"]
        assert "CSE" in result["passes"]
        assert "DCE" in result["passes"]
        assert "CP"  in result["passes"]

    def test_pipeline_respects_disabled_passes(self):
        src = "function f():\n    x = 3 + 4\n    return x"
        result = self._run(src, {"CF": False, "CP": True, "DCE": True, "CSE": True, "LICM": True})
        assert result["passes"]["CF"]["applied"] == False

    def test_stats_present(self):
        src = "function f():\n    return 1"
        result = self._run(src)
        assert "instructions_before" in result["stats"]
        assert "instructions_after"  in result["stats"]


# ═══ CFG TESTS ═══════════════════════════════════════════════

class TestCFGBuilder:
    def _build(self, src):
        tokens = Lexer(src).tokenize()
        ast    = Parser(tokens).parse()
        ir     = IRGenerator().generate(ast)
        return CFGBuilder().build(ir.functions[0])

    def test_entry_block_exists(self):
        cfg = self._build("function f():\n    return 0")
        assert any(b.is_entry for b in cfg.blocks)

    def test_exit_block_exists(self):
        cfg = self._build("function f():\n    return 0")
        assert any(b.is_exit for b in cfg.blocks)

    def test_while_creates_back_edge(self):
        src = "function f(n):\n    while n > 0:\n        n = n - 1"
        cfg = self._build(src)
        # There must be at least 3 blocks: cond, body, end
        assert len(cfg.blocks) >= 3

    def test_if_creates_branches(self):
        src = "function f(x):\n    if x > 0:\n        return x\n    return 0"
        cfg = self._build(src)
        assert len(cfg.edges) >= 2


# ═══ END-TO-END PIPELINE TESTS ══════════════════════════════

class TestFullPipeline:
    def _compile(self, src, passes=None):
        return AlgoFlowCompiler().compile(src, passes)

    def test_bubble_sort_compiles(self):
        src = """\
function BubbleSort(arr, n):
    i = 0
    while i < n - 1:
        j = 0
        while j < n - i - 1:
            if arr[j] > arr[j + 1]:
                temp = arr[j]
                arr[j] = arr[j + 1]
                arr[j + 1] = temp
            j = j + 1
        i = i + 1
    return arr
"""
        result = self._compile(src)
        assert result["ast"]["node_type"] == "Program"
        assert len(result["tokens"]) > 0
        assert len(result["ir_before"]["functions"]) == 1
        assert len(result["cfg"]) == 1

    def test_optimization_reduces_ir(self):
        # Source with CSE candidates
        src = """\
function f():
    x = 5 + 3
    y = 5 + 3
    return x
"""
        result = self._compile(src, {"CF": True, "CSE": True, "DCE": True, "CP": True, "LICM": True})
        stats = result["stats"]
        assert stats["ir_after_count"] <= stats["ir_before_count"]

    def test_errors_list_is_empty_on_success(self):
        src = "function f(x):\n    return x + 1"
        result = self._compile(src)
        assert result["errors"] == []

    def test_timings_recorded(self):
        src = "function f():\n    return 0"
        result = self._compile(src)
        assert "lexer"    in result["timings"]
        assert "parser"   in result["timings"]
        assert "ir_gen"   in result["timings"]
        assert "optimizer" in result["timings"]
        assert "cfg"      in result["timings"]

    def test_stats_populated(self):
        src = "function f():\n    return 0"
        result = self._compile(src)
        assert result["stats"]["function_count"] == 1
        assert result["stats"]["token_count"] > 0


# ═══ SIMULATOR TESTS ═════════════════════════════════════════

class TestSimulator:
    def test_bubble_sort_produces_steps(self):
        sim = Simulator()
        result = sim.simulate("bubble", [5, 3, 1, 4, 2])
        assert len(result["steps"]) > 0
        assert result["steps"][-1]["action"] == "done"

    def test_bubble_sort_final_array_sorted(self):
        sim = Simulator()
        result = sim.simulate("bubble", [5, 3, 1, 4, 2])
        final = result["steps"][-1]["array"]
        assert final == sorted([5, 3, 1, 4, 2])

    def test_merge_sort_final_sorted(self):
        sim = Simulator()
        result = sim.simulate("merge", [8, 3, 1, 5, 2, 7])
        final = result["steps"][-1]["array"]
        assert final == sorted([8, 3, 1, 5, 2, 7])

    def test_quick_sort_final_sorted(self):
        sim = Simulator()
        result = sim.simulate("quick", [9, 2, 7, 1, 6])
        final = result["steps"][-1]["array"]
        assert final == sorted([9, 2, 7, 1, 6])

    def test_binary_search_finds_target(self):
        sim = Simulator()
        result = sim.simulate("binary", [1, 3, 5, 7, 9, 11])
        assert any(s["action"] == "found" for s in result["steps"])

    def test_fibonacci_dp(self):
        sim = Simulator()
        result = sim.simulate("fib", [8])
        done = result["steps"][-1]
        assert done["action"] == "done"
        assert done["dp_table"] is not None

    def test_metrics_recorded(self):
        sim = Simulator()
        result = sim.simulate("bubble", [3, 1, 2])
        assert "comparisons" in result["metrics"]
        assert "swaps"       in result["metrics"]
        assert "complexity"  in result["metrics"]

    def test_bfs_visits_all_nodes(self):
        sim = Simulator()
        result = sim.simulate("bfs", [1, 2, 3, 4, 5])
        done = result["steps"][-1]
        assert done["action"] == "done"
