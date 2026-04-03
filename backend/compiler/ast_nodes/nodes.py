"""
AlgoFlow AST Node Definitions

Every node carries line/col for error reporting and serializes to a dict
for JSON transport to the frontend visualizer.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Any, Union
import json


# ─── Base ────────────────────────────────────────────────────────────────────

@dataclass
class ASTNode:
    node_type: str = field(init=False)
    line: int = 0
    col:  int = 0

    def to_dict(self) -> dict:
        raise NotImplementedError

    def _base(self) -> dict:
        return {"node_type": self.node_type, "line": self.line, "col": self.col}


# ─── Program ─────────────────────────────────────────────────────────────────

@dataclass
class Program(ASTNode):
    body: List[ASTNode] = field(default_factory=list)

    def __post_init__(self): self.node_type = "Program"

    def to_dict(self):
        return {**self._base(), "body": [s.to_dict() for s in self.body]}


# ─── Declarations ────────────────────────────────────────────────────────────

@dataclass
class FunctionDecl(ASTNode):
    name:   str = ""
    params: List[str] = field(default_factory=list)
    body:   List[ASTNode] = field(default_factory=list)

    def __post_init__(self): self.node_type = "FunctionDecl"

    def to_dict(self):
        return {**self._base(), "name": self.name, "params": self.params,
                "body": [s.to_dict() for s in self.body]}


# ─── Statements ──────────────────────────────────────────────────────────────

@dataclass
class AssignStmt(ASTNode):
    target: ASTNode = None
    value:  ASTNode = None
    op:     str = "="           # =, +=, -=, *=, /=

    def __post_init__(self): self.node_type = "AssignStmt"

    def to_dict(self):
        return {**self._base(), "target": self.target.to_dict(),
                "value": self.value.to_dict(), "op": self.op}


@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode] = None

    def __post_init__(self): self.node_type = "ReturnStmt"

    def to_dict(self):
        return {**self._base(), "value": self.value.to_dict() if self.value else None}


@dataclass
class IfStmt(ASTNode):
    condition:   ASTNode = None
    then_body:   List[ASTNode] = field(default_factory=list)
    elif_clauses: List[tuple] = field(default_factory=list)   # [(cond, body), ...]
    else_body:   List[ASTNode] = field(default_factory=list)

    def __post_init__(self): self.node_type = "IfStmt"

    def to_dict(self):
        return {
            **self._base(),
            "condition":    self.condition.to_dict(),
            "then_body":    [s.to_dict() for s in self.then_body],
            "elif_clauses": [(c.to_dict(), [s.to_dict() for s in b]) for c, b in self.elif_clauses],
            "else_body":    [s.to_dict() for s in self.else_body],
        }


@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode = None
    body:      List[ASTNode] = field(default_factory=list)

    def __post_init__(self): self.node_type = "WhileStmt"

    def to_dict(self):
        return {**self._base(), "condition": self.condition.to_dict(),
                "body": [s.to_dict() for s in self.body]}


@dataclass
class ForStmt(ASTNode):
    var:      str = ""
    iterable: ASTNode = None
    body:     List[ASTNode] = field(default_factory=list)

    def __post_init__(self): self.node_type = "ForStmt"

    def to_dict(self):
        return {**self._base(), "var": self.var,
                "iterable": self.iterable.to_dict() if self.iterable else None,
                "body": [s.to_dict() for s in self.body]}


@dataclass
class BreakStmt(ASTNode):
    def __post_init__(self): self.node_type = "BreakStmt"
    def to_dict(self): return self._base()


@dataclass
class ContinueStmt(ASTNode):
    def __post_init__(self): self.node_type = "ContinueStmt"
    def to_dict(self): return self._base()


@dataclass
class ExprStmt(ASTNode):
    expr: ASTNode = None

    def __post_init__(self): self.node_type = "ExprStmt"

    def to_dict(self):
        return {**self._base(), "expr": self.expr.to_dict() if self.expr else None}


# ─── Expressions ─────────────────────────────────────────────────────────────

@dataclass
class BinaryExpr(ASTNode):
    op:    str = ""
    left:  ASTNode = None
    right: ASTNode = None

    def __post_init__(self): self.node_type = "BinaryExpr"

    def to_dict(self):
        return {**self._base(), "op": self.op,
                "left": self.left.to_dict(), "right": self.right.to_dict()}


@dataclass
class UnaryExpr(ASTNode):
    op:    str = ""
    operand: ASTNode = None

    def __post_init__(self): self.node_type = "UnaryExpr"

    def to_dict(self):
        return {**self._base(), "op": self.op, "operand": self.operand.to_dict()}


@dataclass
class CallExpr(ASTNode):
    callee: str = ""
    args:   List[ASTNode] = field(default_factory=list)

    def __post_init__(self): self.node_type = "CallExpr"

    def to_dict(self):
        return {**self._base(), "callee": self.callee,
                "args": [a.to_dict() for a in self.args]}


@dataclass
class IndexExpr(ASTNode):
    obj:   ASTNode = None
    index: ASTNode = None

    def __post_init__(self): self.node_type = "IndexExpr"

    def to_dict(self):
        return {**self._base(), "obj": self.obj.to_dict(), "index": self.index.to_dict()}


@dataclass
class MemberExpr(ASTNode):
    obj:    ASTNode = None
    member: str = ""

    def __post_init__(self): self.node_type = "MemberExpr"

    def to_dict(self):
        return {**self._base(), "obj": self.obj.to_dict(), "member": self.member}


@dataclass
class Identifier(ASTNode):
    name: str = ""

    def __post_init__(self): self.node_type = "Identifier"

    def to_dict(self):
        return {**self._base(), "name": self.name}


@dataclass
class IntLiteral(ASTNode):
    value: int = 0

    def __post_init__(self): self.node_type = "IntLiteral"

    def to_dict(self):
        return {**self._base(), "value": self.value}


@dataclass
class FloatLiteral(ASTNode):
    value: float = 0.0

    def __post_init__(self): self.node_type = "FloatLiteral"

    def to_dict(self):
        return {**self._base(), "value": self.value}


@dataclass
class BoolLiteral(ASTNode):
    value: bool = False

    def __post_init__(self): self.node_type = "BoolLiteral"

    def to_dict(self):
        return {**self._base(), "value": self.value}


@dataclass
class NullLiteral(ASTNode):
    def __post_init__(self): self.node_type = "NullLiteral"
    def to_dict(self): return self._base()


@dataclass
class ArrayLiteral(ASTNode):
    elements: List[ASTNode] = field(default_factory=list)

    def __post_init__(self): self.node_type = "ArrayLiteral"

    def to_dict(self):
        return {**self._base(), "elements": [e.to_dict() for e in self.elements]}
