"""
AlgoFlow IR — Three-Address Code (TAC)

The IR is a list of IRInstruction objects forming basic blocks.
Each instruction is: result = op arg1, arg2   (like LLVM IR or TAC textbooks)

Instruction set:
  ASSIGN    result = arg1
  ADD/SUB/MUL/DIV/MOD   result = arg1 op arg2
  NEG       result = -arg1
  NOT       result = !arg1
  EQ/NE/LT/GT/LE/GE     result = arg1 cmp arg2
  AND/OR    result = arg1 logic arg2
  LABEL     label:
  JUMP      goto label
  JUMP_IF   if arg1 goto label
  JUMP_UNLESS  if not arg1 goto label
  PARAM     push arg1
  CALL      result = call func, nargs
  RETURN    return arg1
  LOAD_IDX  result = arr[idx]
  STORE_IDX arr[idx] = value
  PHI       (SSA — future extension)
  ALLOC     result = alloc size
  COMMENT   metadata
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, List, Dict, Set
import json


class IROpCode(Enum):
    # Data movement
    ASSIGN    = "ASSIGN"
    # Arithmetic
    ADD       = "ADD"
    SUB       = "SUB"
    MUL       = "MUL"
    DIV       = "DIV"
    MOD       = "MOD"
    NEG       = "NEG"
    # Comparison
    EQ        = "EQ"
    NE        = "NE"
    LT        = "LT"
    GT        = "GT"
    LE        = "LE"
    GE        = "GE"
    # Logical
    AND       = "AND"
    OR        = "OR"
    NOT       = "NOT"
    # Control flow
    LABEL     = "LABEL"
    JUMP      = "JUMP"
    JUMP_IF   = "JUMP_IF"
    JUMP_UNLESS = "JUMP_UNLESS"
    # Functions
    PARAM     = "PARAM"
    CALL      = "CALL"
    RETURN    = "RETURN"
    FUNC_BEGIN = "FUNC_BEGIN"
    FUNC_END  = "FUNC_END"
    # Memory
    LOAD_IDX  = "LOAD_IDX"
    STORE_IDX = "STORE_IDX"
    ALLOC     = "ALLOC"
    # Meta
    COMMENT   = "COMMENT"
    NOP       = "NOP"


@dataclass
class IRInstruction:
    op:      IROpCode
    result:  Optional[str] = None   # destination temp/var
    arg1:    Optional[str] = None
    arg2:    Optional[str] = None
    label:   Optional[str] = None   # for LABEL / JUMP targets
    line:    int = 0                # source line
    index:   int = 0                # instruction index in list

    # Optimization metadata
    is_dead:       bool = False     # DCE: marked for removal
    is_eliminated: bool = False     # DCE: actually removed
    opt_note:      str  = ""        # which pass touched this
    original_args: Optional[tuple] = None  # before constant folding

    def to_dict(self) -> dict:
        return {
            "index":        self.index,
            "op":           self.op.value,
            "result":       self.result,
            "arg1":         self.arg1,
            "arg2":         self.arg2,
            "label":        self.label,
            "line":         self.line,
            "is_dead":      self.is_dead,
            "is_eliminated": self.is_eliminated,
            "opt_note":     self.opt_note,
        }

    def __str__(self) -> str:
        parts = [f"[{self.index:03d}]"]
        if self.is_dead:
            parts.append("~~DEAD~~")
        if self.op == IROpCode.LABEL:
            return f"{self.label}:"
        if self.op == IROpCode.COMMENT:
            return f"; {self.arg1}"
        if self.op == IROpCode.JUMP:
            return f"  JUMP  → {self.label}"
        if self.op in (IROpCode.JUMP_IF, IROpCode.JUMP_UNLESS):
            kw = "if" if self.op == IROpCode.JUMP_IF else "unless"
            return f"  {self.op.value}  {kw} {self.arg1} → {self.label}"
        if self.op == IROpCode.RETURN:
            return f"  RETURN {self.arg1 or ''}"
        if self.op == IROpCode.ASSIGN:
            return f"  {self.result} = {self.arg1}"
        if self.op in (IROpCode.ADD, IROpCode.SUB, IROpCode.MUL,
                        IROpCode.DIV, IROpCode.MOD):
            sym = {IROpCode.ADD:'+', IROpCode.SUB:'-', IROpCode.MUL:'*',
                   IROpCode.DIV:'/', IROpCode.MOD:'%'}[self.op]
            return f"  {self.result} = {self.arg1} {sym} {self.arg2}"
        if self.op in (IROpCode.EQ, IROpCode.NE, IROpCode.LT,
                        IROpCode.GT, IROpCode.LE, IROpCode.GE):
            sym = {IROpCode.EQ:'==', IROpCode.NE:'!=', IROpCode.LT:'<',
                   IROpCode.GT:'>', IROpCode.LE:'<=', IROpCode.GE:'>='}[self.op]
            return f"  {self.result} = {self.arg1} {sym} {self.arg2}"
        if self.op == IROpCode.LOAD_IDX:
            return f"  {self.result} = {self.arg1}[{self.arg2}]"
        if self.op == IROpCode.STORE_IDX:
            return f"  {self.result}[{self.arg1}] = {self.arg2}"
        if self.op == IROpCode.CALL:
            return f"  {self.result} = call {self.arg1}({self.arg2})"
        if self.op == IROpCode.PARAM:
            return f"  param {self.arg1}"
        if self.op in (IROpCode.FUNC_BEGIN, IROpCode.FUNC_END):
            return f"// {self.op.value} {self.label}"
        return f"  {self.op.value} {self.result or ''} {self.arg1 or ''} {self.arg2 or ''}"


@dataclass
class IRFunction:
    name:   str
    params: List[str] = field(default_factory=list)
    instructions: List[IRInstruction] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name":         self.name,
            "params":       self.params,
            "instructions": [i.to_dict() for i in self.instructions],
        }

    def __str__(self) -> str:
        lines = [f"function {self.name}({', '.join(self.params)}):"]
        for inst in self.instructions:
            lines.append(str(inst))
        return '\n'.join(lines)


@dataclass
class IRProgram:
    functions: List[IRFunction] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"functions": [f.to_dict() for f in self.functions]}

    def __str__(self) -> str:
        return '\n\n'.join(str(f) for f in self.functions)
