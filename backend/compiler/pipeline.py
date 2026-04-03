"""
AlgoFlow Compiler Pipeline

Orchestrates the full compilation:
  Source → Lexer → Parser → AST → IRGen → Optimizer → CFG Builder → JSON output
"""

from __future__ import annotations
import time
import traceback
from typing import Dict, Any, List

from .lexer.lexer import Lexer
from .parser.parser import Parser, ParseError
from .ir.generator import IRGenerator
from .optimizer.passes import OptimizationPipeline
from .cfg.cfg_builder import CFGBuilder


class CompilerError(Exception):
    def __init__(self, stage: str, message: str, detail: str = ""):
        super().__init__(message)
        self.stage   = stage
        self.message = message
        self.detail  = detail

    def to_dict(self):
        return {"stage": self.stage, "message": self.message, "detail": self.detail}


class AlgoFlowCompiler:
    """
    Full compiler pipeline from pseudocode source to structured output
    suitable for the AlgoFlow frontend visualizer.
    """

    def compile(self, source: str, enabled_passes: Dict[str, bool] = None) -> Dict[str, Any]:
        """
        Main entry point. Returns a rich dict with:
          - tokens:       flat list of lexer tokens
          - ast:          recursive dict (for AST visualizer)
          - ir_before:    list of IR instructions pre-optimization
          - ir_after:     list of IR instructions post-optimization
          - passes:       per-pass change logs and statistics
          - cfg:          control flow graphs per function
          - stats:        summary metrics
          - errors:       list of any non-fatal issues
        """
        if enabled_passes is None:
            enabled_passes = {"DCE": True, "CP": True, "CF": True,
                               "CSE": True, "LICM": True}

        result: Dict[str, Any] = {
            "source":     source,
            "tokens":     [],
            "ast":        {},
            "ir_before":  [],
            "ir_after":   [],
            "passes":     {},
            "cfg":        [],
            "stats":      {},
            "errors":     [],
            "timings":    {},
        }

        # ── Stage 1: Lexing ────────────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            lexer  = Lexer(source)
            tokens = lexer.tokenize()
            result["tokens"] = [
                {"type": t.type.name, "value": t.value, "line": t.line, "col": t.column}
                for t in tokens
            ]
        except Exception as e:
            raise CompilerError("lexer", str(e), traceback.format_exc())
        result["timings"]["lexer"] = round((time.perf_counter() - t0) * 1000, 2)

        # ── Stage 2: Parsing ───────────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            parser = Parser(tokens)
            ast    = parser.parse()
            result["ast"] = ast.to_dict()
        except ParseError as e:
            raise CompilerError("parser", str(e))
        except Exception as e:
            raise CompilerError("parser", str(e), traceback.format_exc())
        result["timings"]["parser"] = round((time.perf_counter() - t0) * 1000, 2)

        # ── Stage 3: IR Generation ─────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            irgen   = IRGenerator()
            ir_prog = irgen.generate(ast)
            result["ir_before"] = ir_prog.to_dict()
        except Exception as e:
            raise CompilerError("ir_gen", str(e), traceback.format_exc())
        result["timings"]["ir_gen"] = round((time.perf_counter() - t0) * 1000, 2)

        # ── Stage 4: Optimization ──────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            pipeline    = OptimizationPipeline(enabled_passes)
            opt_results = {}
            ir_after_all = []

            for func in ir_prog.functions:
                func_result = pipeline.run(func)
                opt_results[func.name] = func_result
                ir_after_all.append({
                    "function": func.name,
                    "before":   func_result["before"],
                    "after":    func_result["after"],
                    "passes":   func_result["passes"],
                    "stats":    func_result["stats"],
                })

            result["passes"]   = opt_results
            result["ir_after"] = ir_after_all

            # Aggregate stats
            total_before = sum(r["stats"]["instructions_before"] for r in opt_results.values())
            total_after  = sum(r["stats"]["instructions_after"]  for r in opt_results.values())
            total_elim   = sum(r["stats"]["eliminated"]          for r in opt_results.values())
            result["stats"]["ir_before_count"] = total_before
            result["stats"]["ir_after_count"]  = total_after
            result["stats"]["ir_eliminated"]   = total_elim
            result["stats"]["reduction_pct"]   = (
                round((1 - total_after / total_before) * 100, 1)
                if total_before > 0 else 0
            )

        except Exception as e:
            result["errors"].append({"stage": "optimizer", "message": str(e)})
        result["timings"]["optimizer"] = round((time.perf_counter() - t0) * 1000, 2)

        # ── Stage 5: CFG Building ──────────────────────────────────────────
        t0 = time.perf_counter()
        try:
            cfg_builder = CFGBuilder()
            cfgs = []
            for func in ir_prog.functions:
                cfg = cfg_builder.build(func)
                cfgs.append(cfg.to_dict())
            result["cfg"] = cfgs
            result["stats"]["total_blocks"] = sum(len(c["blocks"]) for c in cfgs)
            result["stats"]["total_edges"]  = sum(len(c["edges"])  for c in cfgs)
        except Exception as e:
            result["errors"].append({"stage": "cfg", "message": str(e)})
        result["timings"]["cfg"] = round((time.perf_counter() - t0) * 1000, 2)

        # ── Summary ────────────────────────────────────────────────────────
        result["stats"]["function_count"] = len(ir_prog.functions)
        result["stats"]["token_count"]    = len(tokens)
        result["stats"]["total_time_ms"]  = round(sum(result["timings"].values()), 2)

        return result
