"""
AlgoFlow IR Generator — AST → Three-Address Code

Walks the AST and emits IRInstruction objects.
Uses a temp variable counter (%t0, %t1, …) and label counter.
"""

from __future__ import annotations
from typing import List, Optional
from ..ast_nodes.nodes import *
from .ir import IRInstruction, IROpCode, IRFunction, IRProgram


class IRGenerator:
    def __init__(self):
        self._temp_counter  = 0
        self._label_counter = 0
        self._instructions: List[IRInstruction] = []
        self._current_func: Optional[str] = None
        self._functions: List[IRFunction] = []
        self._source_line = 0

    # ─── Helpers ──────────────────────────────────────────────────────────

    def _new_temp(self) -> str:
        name = f"%t{self._temp_counter}"
        self._temp_counter += 1
        return name

    def _new_label(self, prefix: str = "L") -> str:
        name = f"{prefix}_{self._label_counter}"
        self._label_counter += 1
        return name

    def _emit(self, op: IROpCode, result=None, arg1=None, arg2=None, label=None) -> IRInstruction:
        inst = IRInstruction(
            op=op, result=result, arg1=arg1, arg2=arg2,
            label=label, line=self._source_line,
            index=len(self._instructions)
        )
        self._instructions.append(inst)
        return inst

    def _finalize_function(self, name: str, params: List[str]):
        func = IRFunction(name=name, params=params,
                          instructions=list(self._instructions))
        # Re-index
        for i, inst in enumerate(func.instructions):
            inst.index = i
        self._functions.append(func)
        self._instructions.clear()

    # ─── Top-Level ────────────────────────────────────────────────────────

    def generate(self, program: Program) -> IRProgram:
        # If there are top-level statements (not wrapped in functions), wrap them
        top_stmts = [s for s in program.body if not isinstance(s, FunctionDecl)]
        funcs     = [s for s in program.body if isinstance(s, FunctionDecl)]

        for func in funcs:
            self._gen_function(func)

        if top_stmts:
            # Wrap bare statements in a synthetic "main" function
            self._emit(IROpCode.FUNC_BEGIN, label="main")
            for stmt in top_stmts:
                self._gen_stmt(stmt)
            self._emit(IROpCode.FUNC_END, label="main")
            self._finalize_function("main", [])

        return IRProgram(functions=self._functions)

    # ─── Function ─────────────────────────────────────────────────────────

    def _gen_function(self, node: FunctionDecl):
        self._current_func = node.name
        self._emit(IROpCode.FUNC_BEGIN, label=node.name)
        for stmt in node.body:
            self._gen_stmt(stmt)
        # Ensure a return at the end
        if not self._instructions or self._instructions[-1].op != IROpCode.RETURN:
            self._emit(IROpCode.RETURN, arg1=None)
        self._emit(IROpCode.FUNC_END, label=node.name)
        self._finalize_function(node.name, node.params)

    # ─── Statements ───────────────────────────────────────────────────────

    def _gen_stmt(self, node: ASTNode):
        self._source_line = getattr(node, 'line', 0)

        if isinstance(node, AssignStmt):
            self._gen_assign(node)
        elif isinstance(node, ReturnStmt):
            val = self._gen_expr(node.value) if node.value else None
            self._emit(IROpCode.RETURN, arg1=val)
        elif isinstance(node, IfStmt):
            self._gen_if(node)
        elif isinstance(node, WhileStmt):
            self._gen_while(node)
        elif isinstance(node, ForStmt):
            self._gen_for(node)
        elif isinstance(node, BreakStmt):
            # Handled by loop context — for now emit a JUMP placeholder
            self._emit(IROpCode.JUMP, label="__break__")
        elif isinstance(node, ContinueStmt):
            self._emit(IROpCode.JUMP, label="__continue__")
        elif isinstance(node, ExprStmt):
            self._gen_expr(node.expr)
        elif isinstance(node, FunctionDecl):
            self._gen_function(node)

    # ─── Assignment ───────────────────────────────────────────────────────

    def _gen_assign(self, node: AssignStmt):
        rhs = self._gen_expr(node.value)

        if node.op != "=":
            # Compound assignment: +=, -=, *=, /=
            lhs_val = self._gen_expr(node.target)
            op_map = {"+=": IROpCode.ADD, "-=": IROpCode.SUB,
                      "*=": IROpCode.MUL, "/=": IROpCode.DIV}
            tmp = self._new_temp()
            self._emit(op_map[node.op], result=tmp, arg1=lhs_val, arg2=rhs)
            rhs = tmp

        target = node.target
        if isinstance(target, Identifier):
            self._emit(IROpCode.ASSIGN, result=target.name, arg1=rhs)
        elif isinstance(target, IndexExpr):
            arr  = self._gen_expr(target.obj)
            idx  = self._gen_expr(target.index)
            self._emit(IROpCode.STORE_IDX, result=arr, arg1=idx, arg2=rhs)
        else:
            self._emit(IROpCode.ASSIGN, result=str(target), arg1=rhs)

    # ─── If Statement ─────────────────────────────────────────────────────

    def _gen_if(self, node: IfStmt):
        end_label   = self._new_label("if_end")
        false_label = self._new_label("if_false")

        cond = self._gen_expr(node.condition)
        self._emit(IROpCode.JUMP_UNLESS, arg1=cond, label=false_label)

        for stmt in node.then_body:
            self._gen_stmt(stmt)
        self._emit(IROpCode.JUMP, label=end_label)

        self._emit(IROpCode.LABEL, label=false_label)

        for ec, eb in node.elif_clauses:
            next_label = self._new_label("elif_false")
            ec_val = self._gen_expr(ec)
            self._emit(IROpCode.JUMP_UNLESS, arg1=ec_val, label=next_label)
            for stmt in eb:
                self._gen_stmt(stmt)
            self._emit(IROpCode.JUMP, label=end_label)
            self._emit(IROpCode.LABEL, label=next_label)

        for stmt in node.else_body:
            self._gen_stmt(stmt)

        self._emit(IROpCode.LABEL, label=end_label)

    # ─── While Statement ──────────────────────────────────────────────────

    def _gen_while(self, node: WhileStmt):
        loop_label = self._new_label("while_cond")
        body_label = self._new_label("while_body")
        end_label  = self._new_label("while_end")

        self._emit(IROpCode.LABEL, label=loop_label)
        cond = self._gen_expr(node.condition)
        self._emit(IROpCode.JUMP_UNLESS, arg1=cond, label=end_label)
        self._emit(IROpCode.LABEL, label=body_label)

        # Patch break/continue labels
        for stmt in node.body:
            self._gen_stmt(stmt)
        # Patch placeholder jumps
        for inst in self._instructions:
            if inst.op == IROpCode.JUMP and inst.label == "__break__":
                inst.label = end_label
            if inst.op == IROpCode.JUMP and inst.label == "__continue__":
                inst.label = loop_label

        self._emit(IROpCode.JUMP, label=loop_label)
        self._emit(IROpCode.LABEL, label=end_label)

    # ─── For Statement ────────────────────────────────────────────────────

    def _gen_for(self, node: ForStmt):
        iter_val   = self._gen_expr(node.iterable)
        idx_temp   = self._new_temp()
        len_temp   = self._new_temp()
        loop_label = self._new_label("for_cond")
        end_label  = self._new_label("for_end")

        self._emit(IROpCode.ASSIGN, result=idx_temp, arg1="0")
        self._emit(IROpCode.CALL, result=len_temp, arg1="len", arg2=iter_val)
        self._emit(IROpCode.LABEL, label=loop_label)

        cond_tmp = self._new_temp()
        self._emit(IROpCode.LT, result=cond_tmp, arg1=idx_temp, arg2=len_temp)
        self._emit(IROpCode.JUMP_UNLESS, arg1=cond_tmp, label=end_label)

        # Load element
        elem_tmp = self._new_temp()
        self._emit(IROpCode.LOAD_IDX, result=elem_tmp, arg1=iter_val, arg2=idx_temp)
        self._emit(IROpCode.ASSIGN, result=node.var, arg1=elem_tmp)

        for stmt in node.body:
            self._gen_stmt(stmt)

        inc_tmp = self._new_temp()
        self._emit(IROpCode.ADD, result=inc_tmp, arg1=idx_temp, arg2="1")
        self._emit(IROpCode.ASSIGN, result=idx_temp, arg1=inc_tmp)
        self._emit(IROpCode.JUMP, label=loop_label)
        self._emit(IROpCode.LABEL, label=end_label)

    # ─── Expressions ──────────────────────────────────────────────────────

    def _gen_expr(self, node: ASTNode) -> str:
        """Returns the name of the register/variable holding the result."""

        if isinstance(node, IntLiteral):
            return str(node.value)

        if isinstance(node, FloatLiteral):
            return str(node.value)

        if isinstance(node, BoolLiteral):
            return "1" if node.value else "0"

        if isinstance(node, NullLiteral):
            return "null"

        if isinstance(node, Identifier):
            return node.name

        if isinstance(node, ArrayLiteral):
            tmp = self._new_temp()
            self._emit(IROpCode.ALLOC, result=tmp, arg1=str(len(node.elements)))
            for i, elem in enumerate(node.elements):
                v = self._gen_expr(elem)
                self._emit(IROpCode.STORE_IDX, result=tmp, arg1=str(i), arg2=v)
            return tmp

        if isinstance(node, BinaryExpr):
            return self._gen_binary(node)

        if isinstance(node, UnaryExpr):
            operand = self._gen_expr(node.operand)
            tmp = self._new_temp()
            if node.op == '-':
                self._emit(IROpCode.NEG, result=tmp, arg1=operand)
            else:
                self._emit(IROpCode.NOT, result=tmp, arg1=operand)
            return tmp

        if isinstance(node, CallExpr):
            for arg in node.args:
                v = self._gen_expr(arg)
                self._emit(IROpCode.PARAM, arg1=v)
            tmp = self._new_temp()
            self._emit(IROpCode.CALL, result=tmp, arg1=node.callee, arg2=str(len(node.args)))
            return tmp

        if isinstance(node, IndexExpr):
            arr = self._gen_expr(node.obj)
            idx = self._gen_expr(node.index)
            tmp = self._new_temp()
            self._emit(IROpCode.LOAD_IDX, result=tmp, arg1=arr, arg2=idx)
            return tmp

        if isinstance(node, MemberExpr):
            obj = self._gen_expr(node.obj)
            return f"{obj}.{node.member}"

        return "undefined"

    def _gen_binary(self, node: BinaryExpr) -> str:
        left  = self._gen_expr(node.left)
        right = self._gen_expr(node.right)
        tmp   = self._new_temp()

        OP_MAP = {
            '+':  IROpCode.ADD,   '-':  IROpCode.SUB,
            '*':  IROpCode.MUL,   '/':  IROpCode.DIV,
            '%':  IROpCode.MOD,   '//': IROpCode.DIV,
            '==': IROpCode.EQ,    '!=': IROpCode.NE,
            '<':  IROpCode.LT,    '>':  IROpCode.GT,
            '<=': IROpCode.LE,    '>=': IROpCode.GE,
            'and': IROpCode.AND,  'or': IROpCode.OR,
        }
        op = OP_MAP.get(node.op, IROpCode.ADD)
        self._emit(op, result=tmp, arg1=left, arg2=right)
        return tmp
