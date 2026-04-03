"""
AlgoFlow Optimizer — Classical Compiler Optimization Passes

Implements five passes in the LLVM-inspired style, each operating on IRFunction:

  1. Dead Code Elimination (DCE)
     Marks instructions whose results are never used.

  2. Constant Propagation (CP)
     Substitutes known constants for variable references.

  3. Constant Folding (CF)
     Evaluates constant binary expressions at compile time.

  4. Common Subexpression Elimination (CSE)
     Replaces repeated computations with their first result.

  5. Loop Invariant Code Motion (LICM)
     Hoists loop-invariant computations before the loop.

Each pass returns (new_instructions, change_log) where change_log is a list
of dicts describing what changed (for the frontend visualization).
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Set, Optional
from copy import deepcopy
import math

from ..ir.ir import IRInstruction, IROpCode, IRFunction


ChangeLog = List[Dict]


# ─── Base Pass ───────────────────────────────────────────────────────────────

class OptimizationPass:
    name: str = "base"
    description: str = ""

    def run(self, func: IRFunction) -> Tuple[IRFunction, ChangeLog]:
        raise NotImplementedError

    def _clone(self, func: IRFunction) -> IRFunction:
        return deepcopy(func)


# ─── 1. Dead Code Elimination ────────────────────────────────────────────────

class DeadCodeElimination(OptimizationPass):
    name = "DCE"
    description = ("Removes instructions whose computed values are never "
                   "subsequently used. Iterates to fixed point.")

    def run(self, func: IRFunction) -> Tuple[IRFunction, ChangeLog]:
        new_func = self._clone(func)
        insts = new_func.instructions
        changes: ChangeLog = []

        # Collect all opcodes that have observable side effects
        SIDE_EFFECT_OPS = {
            IROpCode.STORE_IDX, IROpCode.RETURN, IROpCode.CALL,
            IROpCode.PARAM, IROpCode.JUMP, IROpCode.JUMP_IF,
            IROpCode.JUMP_UNLESS, IROpCode.LABEL,
            IROpCode.FUNC_BEGIN, IROpCode.FUNC_END, IROpCode.NOP,
        }

        changed = True
        while changed:
            changed = False
            # Build use set: all arg1/arg2 values referenced
            used: Set[str] = set()
            for inst in insts:
                if inst.is_eliminated:
                    continue
                for v in (inst.arg1, inst.arg2):
                    if v and not v.lstrip('-').isdigit() and v not in ('null', 'undefined'):
                        used.add(v)
                if inst.op in (IROpCode.JUMP, IROpCode.JUMP_IF,
                               IROpCode.JUMP_UNLESS):
                    if inst.label:
                        used.add(inst.label)

            for inst in insts:
                if inst.is_eliminated:
                    continue
                if inst.op in SIDE_EFFECT_OPS:
                    continue
                if inst.result and inst.result not in used:
                    inst.is_dead = True
                    inst.is_eliminated = True
                    inst.opt_note = "DCE"
                    changes.append({
                        "type": "eliminated",
                        "index": inst.index,
                        "instruction": str(inst),
                        "reason": f"result '{inst.result}' never used"
                    })
                    changed = True

        return new_func, changes


# ─── 2. Constant Propagation ─────────────────────────────────────────────────

class ConstantPropagation(OptimizationPass):
    name = "CP"
    description = ("Tracks variables that are assigned a single constant value "
                   "and substitutes that constant wherever the variable is read.")

    def run(self, func: IRFunction) -> Tuple[IRFunction, ChangeLog]:
        new_func = self._clone(func)
        insts = new_func.instructions
        changes: ChangeLog = []

        # Simple intra-function flow: collect definitely-constant vars
        constants: Dict[str, str] = {}

        for inst in insts:
            if inst.is_eliminated:
                continue

            # Substitute in args
            for attr in ('arg1', 'arg2'):
                val = getattr(inst, attr)
                if val and val in constants:
                    old = val
                    setattr(inst, attr, constants[val])
                    inst.opt_note = (inst.opt_note + " CP") if inst.opt_note else "CP"
                    changes.append({
                        "type": "substituted",
                        "index": inst.index,
                        "variable": old,
                        "replaced_with": constants[val],
                    })

            # Track new constants from ASSIGN of literal
            if inst.op == IROpCode.ASSIGN and inst.arg1 is not None:
                val = inst.arg1
                if val.lstrip('-').replace('.', '', 1).isdigit():
                    constants[inst.result] = val
                else:
                    # Assigned a non-const: remove from constants if present
                    constants.pop(inst.result, None)

        return new_func, changes


# ─── 3. Constant Folding ─────────────────────────────────────────────────────

class ConstantFolding(OptimizationPass):
    name = "CF"
    description = ("Evaluates arithmetic and comparison expressions whose "
                   "operands are all compile-time constants.")

    ARITH_OPS = {
        IROpCode.ADD, IROpCode.SUB, IROpCode.MUL,
        IROpCode.DIV, IROpCode.MOD,
    }
    CMP_OPS = {
        IROpCode.EQ, IROpCode.NE, IROpCode.LT,
        IROpCode.GT, IROpCode.LE, IROpCode.GE,
    }

    def _is_const(self, v: Optional[str]) -> bool:
        if v is None:
            return False
        try:
            float(v)
            return True
        except ValueError:
            return False

    def _fold(self, op: IROpCode, a: str, b: str) -> Optional[str]:
        try:
            fa, fb = float(a), float(b)
        except ValueError:
            return None

        if op == IROpCode.ADD:  result = fa + fb
        elif op == IROpCode.SUB: result = fa - fb
        elif op == IROpCode.MUL: result = fa * fb
        elif op == IROpCode.DIV:
            if fb == 0: return None
            result = fa / fb
        elif op == IROpCode.MOD:
            if fb == 0: return None
            result = fa % fb
        elif op == IROpCode.EQ:  result = int(fa == fb)
        elif op == IROpCode.NE:  result = int(fa != fb)
        elif op == IROpCode.LT:  result = int(fa < fb)
        elif op == IROpCode.GT:  result = int(fa > fb)
        elif op == IROpCode.LE:  result = int(fa <= fb)
        elif op == IROpCode.GE:  result = int(fa >= fb)
        else: return None

        if result == int(result):
            return str(int(result))
        return str(round(result, 6))

    def run(self, func: IRFunction) -> Tuple[IRFunction, ChangeLog]:
        new_func = self._clone(func)
        changes:  ChangeLog = []

        for inst in new_func.instructions:
            if inst.is_eliminated:
                continue
            if inst.op not in (self.ARITH_OPS | self.CMP_OPS):
                continue
            if not (self._is_const(inst.arg1) and self._is_const(inst.arg2)):
                continue

            folded = self._fold(inst.op, inst.arg1, inst.arg2)
            if folded is not None:
                old_expr = f"{inst.arg1} {inst.op.value} {inst.arg2}"
                inst.original_args = (inst.arg1, inst.arg2, inst.op.value)
                # Replace instruction with a simple assign
                inst.op   = IROpCode.ASSIGN
                inst.arg1 = folded
                inst.arg2 = None
                inst.opt_note = (inst.opt_note + " CF") if inst.opt_note else "CF"
                changes.append({
                    "type": "folded",
                    "index": inst.index,
                    "expression": old_expr,
                    "result": folded,
                })

        return new_func, changes


# ─── 4. Common Subexpression Elimination ─────────────────────────────────────

class CommonSubexpressionElimination(OptimizationPass):
    name = "CSE"
    description = ("Detects identical computations and replaces later occurrences "
                   "with the result of the first, avoiding redundant work.")

    ELIGIBLE_OPS = {
        IROpCode.ADD, IROpCode.SUB, IROpCode.MUL, IROpCode.DIV,
        IROpCode.MOD, IROpCode.EQ,  IROpCode.NE,  IROpCode.LT,
        IROpCode.GT,  IROpCode.LE,  IROpCode.GE,  IROpCode.AND, IROpCode.OR,
    }

    def run(self, func: IRFunction) -> Tuple[IRFunction, ChangeLog]:
        new_func = self._clone(func)
        changes:  ChangeLog = []

        # expr_map: (op, arg1, arg2) → result_temp
        expr_map: Dict[tuple, str] = {}

        for inst in new_func.instructions:
            if inst.is_eliminated:
                continue
            if inst.op not in self.ELIGIBLE_OPS:
                continue

            key = (inst.op, inst.arg1, inst.arg2)

            if key in expr_map:
                # Replace this instruction with an assign from the earlier result
                earlier = expr_map[key]
                old_str = str(inst)
                inst.original_args = (inst.arg1, inst.arg2, inst.op.value)
                inst.op   = IROpCode.ASSIGN
                inst.arg1 = earlier
                inst.arg2 = None
                inst.opt_note = (inst.opt_note + " CSE") if inst.opt_note else "CSE"
                changes.append({
                    "type": "eliminated_cse",
                    "index": inst.index,
                    "original": old_str,
                    "replaced_with": earlier,
                })
            else:
                if inst.result:
                    expr_map[key] = inst.result

        return new_func, changes


# ─── 5. Loop Invariant Code Motion ───────────────────────────────────────────

class LoopInvariantCodeMotion(OptimizationPass):
    name = "LICM"
    description = ("Identifies loop-invariant computations — those that produce "
                   "the same value on every iteration — and hoists them before "
                   "the loop header.")

    def run(self, func: IRFunction) -> Tuple[IRFunction, ChangeLog]:
        new_func = self._clone(func)
        insts    = new_func.instructions
        changes: ChangeLog = []

        # Find loop regions: between while_cond label and matching while_end
        loops = self._find_loops(insts)
        hoisted_before: List[Tuple[int, IRInstruction]] = []  # (insert_pos, inst)

        for (header_idx, body_start, end_idx) in loops:
            loop_body = insts[body_start:end_idx]
            # Compute definitions inside the loop
            loop_defs: Set[str] = set()
            for inst in loop_body:
                if inst.result:
                    loop_defs.add(inst.result)

            # Find invariant instructions: result not in loop_defs, args not in loop_defs
            for inst in loop_body:
                if inst.is_eliminated:
                    continue
                if inst.op in {IROpCode.LABEL, IROpCode.JUMP, IROpCode.JUMP_IF,
                                IROpCode.JUMP_UNLESS, IROpCode.RETURN,
                                IROpCode.STORE_IDX, IROpCode.CALL,
                                IROpCode.FUNC_BEGIN, IROpCode.FUNC_END}:
                    continue
                if inst.op not in {IROpCode.ADD, IROpCode.SUB, IROpCode.MUL,
                                    IROpCode.DIV, IROpCode.MOD}:
                    continue
                arg1_invariant = not inst.arg1 or inst.arg1 not in loop_defs or inst.arg1.lstrip('-').isdigit()
                arg2_invariant = not inst.arg2 or inst.arg2 not in loop_defs or inst.arg2.lstrip('-').isdigit()

                if arg1_invariant and arg2_invariant and inst.result not in loop_defs:
                    hoisted_before.append((header_idx, deepcopy(inst)))
                    inst.is_eliminated = True
                    inst.opt_note = "LICM"
                    changes.append({
                        "type": "hoisted",
                        "index": inst.index,
                        "instruction": str(inst),
                        "hoisted_before": header_idx,
                    })

        # Insert hoisted instructions before their respective loop headers
        offset = 0
        for insert_pos, hoisted_inst in sorted(hoisted_before, key=lambda x: x[0]):
            hoisted_inst.opt_note = "LICM↑"
            insts.insert(insert_pos + offset, hoisted_inst)
            offset += 1

        # Re-index
        for i, inst in enumerate(insts):
            inst.index = i

        return new_func, changes

    def _find_loops(self, insts: List[IRInstruction]):
        """Returns list of (header_idx, body_start, end_idx) tuples."""
        loops = []
        label_to_idx = {}

        for i, inst in enumerate(insts):
            if inst.op == IROpCode.LABEL and inst.label:
                label_to_idx[inst.label] = i

        for i, inst in enumerate(insts):
            if inst.op != IROpCode.LABEL:
                continue
            lbl = inst.label or ""
            if not lbl.startswith("while_cond"):
                continue
            # Find corresponding end label
            base = lbl.replace("while_cond", "while_end")
            end_idx = label_to_idx.get(base)
            body_lbl = lbl.replace("while_cond", "while_body")
            body_idx = label_to_idx.get(body_lbl, i + 2)
            if end_idx:
                loops.append((i, body_idx, end_idx))

        return loops


# ─── Pipeline ────────────────────────────────────────────────────────────────

class OptimizationPipeline:
    PASS_CLASSES = {
        "DCE":  DeadCodeElimination,
        "CP":   ConstantPropagation,
        "CF":   ConstantFolding,
        "CSE":  CommonSubexpressionElimination,
        "LICM": LoopInvariantCodeMotion,
    }

    def __init__(self, enabled_passes: Dict[str, bool] = None):
        self.enabled = enabled_passes or {k: True for k in self.PASS_CLASSES}

    def run(self, func: IRFunction) -> Dict:
        """
        Runs all enabled passes in order. Returns full pipeline result:
        {
          "before": [...instructions...],
          "after":  [...instructions...],
          "passes": { "DCE": {applied, changes}, ... }
        }
        """
        before_insts = [deepcopy(i) for i in func.instructions]
        current_func = deepcopy(func)
        pass_results = {}

        # Run in canonical order: CF first (feeds CP), then CP, CSE, LICM, DCE last
        ORDER = ["CF", "CP", "CSE", "LICM", "DCE"]

        for pass_name in ORDER:
            if not self.enabled.get(pass_name, True):
                pass_results[pass_name] = {
                    "applied": False,
                    "changes": [],
                    "description": self.PASS_CLASSES[pass_name].description,
                    "name": self.PASS_CLASSES[pass_name].name,
                }
                continue

            pass_cls = self.PASS_CLASSES[pass_name]
            opt_pass = pass_cls()
            current_func, changes = opt_pass.run(current_func)
            pass_results[pass_name] = {
                "applied": True,
                "changes": changes,
                "description": pass_cls.description,
                "name": pass_cls.name,
                "change_count": len(changes),
            }

        after_insts = [i for i in current_func.instructions if not i.is_eliminated]

        return {
            "before":       [i.to_dict() for i in before_insts],
            "after":        [i.to_dict() for i in after_insts],
            "after_all":    [i.to_dict() for i in current_func.instructions],
            "passes":       pass_results,
            "stats": {
                "instructions_before": len([i for i in before_insts if i.op != IROpCode.COMMENT]),
                "instructions_after":  len(after_insts),
                "eliminated":          sum(1 for i in current_func.instructions if i.is_eliminated),
                "total_changes":       sum(len(v["changes"]) for v in pass_results.values()),
            }
        }
