"""
AlgoFlow Parser — Recursive Descent

Precedence (low → high):
  assignment  =, +=, -=, *=, /=
  logical     or, and
  comparison  ==, !=, <, >, <=, >=
  additive    +, -
  mult        *, /, %, //
  unary       not, -
  postfix     call(), index[], .member
  primary     literals, identifiers, (expr)
"""

from __future__ import annotations
from typing import List, Optional, Tuple

from ..lexer.tokens import Token, TokenType
from ..ast_nodes.nodes import *


class ParseError(Exception):
    def __init__(self, msg: str, token: Token):
        super().__init__(f"ParseError at {token.line}:{token.column} — {msg} (got {token.type.name} {token.value!r})")
        self.token = token


class Parser:
    def __init__(self, tokens: List[Token]):
        # Strip comment tokens and collapse multiple newlines
        self.tokens = self._clean(tokens)
        self.pos = 0

    # ─── Token Stream Helpers ─────────────────────────────────────────────

    def _clean(self, tokens: List[Token]) -> List[Token]:
        result = []
        prev_type = None
        for t in tokens:
            if t.type == TokenType.COMMENT:
                continue
            # Collapse consecutive NEWLINEs
            if t.type == TokenType.NEWLINE and prev_type == TokenType.NEWLINE:
                continue
            if t.type == TokenType.NEWLINE and prev_type in (TokenType.INDENT, TokenType.DEDENT):
                continue
            result.append(t)
            prev_type = t.type
        return result

    def _peek(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token(TokenType.EOF, "", 0, 0)

    def _peek2(self) -> Token:
        return self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else Token(TokenType.EOF, "", 0, 0)

    def _advance(self) -> Token:
        t = self._peek()
        self.pos += 1
        return t

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _match(self, *types: TokenType) -> Optional[Token]:
        if self._peek().type in types:
            return self._advance()
        return None

    def _expect(self, type_: TokenType, msg: str = "") -> Token:
        if self._peek().type == type_:
            return self._advance()
        raise ParseError(msg or f"Expected {type_.name}", self._peek())

    def _skip_newlines(self):
        while self._check(TokenType.NEWLINE):
            self._advance()

    # ─── Entry Point ──────────────────────────────────────────────────────

    def parse(self) -> Program:
        prog = Program(line=1, col=1)
        self._skip_newlines()
        while not self._at_end():
            stmt = self._parse_top_level()
            if stmt:
                prog.body.append(stmt)
            self._skip_newlines()
        return prog

    # ─── Top-level ────────────────────────────────────────────────────────

    def _parse_top_level(self) -> Optional[ASTNode]:
        if self._check(TokenType.FUNCTION):
            return self._parse_function()
        return self._parse_stmt()

    # ─── Function Declaration ─────────────────────────────────────────────

    def _parse_function(self) -> FunctionDecl:
        tok = self._expect(TokenType.FUNCTION)
        name_tok = self._expect(TokenType.IDENTIFIER, "Expected function name")
        self._expect(TokenType.LPAREN, "Expected '(' after function name")

        params: List[str] = []
        while not self._check(TokenType.RPAREN) and not self._at_end():
            params.append(self._expect(TokenType.IDENTIFIER, "Expected parameter name").value)
            if not self._match(TokenType.COMMA):
                break
        self._expect(TokenType.RPAREN, "Expected ')' after parameters")

        # Optional return type annotation
        if self._match(TokenType.ARROW):
            self._advance()  # skip type name

        self._expect(TokenType.COLON, "Expected ':' after function signature")
        self._skip_newlines()
        body = self._parse_block()

        return FunctionDecl(name=name_tok.value, params=params, body=body,
                            line=tok.line, col=tok.column)

    # ─── Block ────────────────────────────────────────────────────────────

    def _parse_block(self) -> List[ASTNode]:
        stmts: List[ASTNode] = []
        self._expect(TokenType.INDENT, "Expected indented block")
        self._skip_newlines()
        while not self._check(TokenType.DEDENT) and not self._at_end():
            s = self._parse_stmt()
            if s:
                stmts.append(s)
            self._skip_newlines()
        self._match(TokenType.DEDENT)
        return stmts

    # ─── Statements ───────────────────────────────────────────────────────

    def _parse_stmt(self) -> Optional[ASTNode]:
        tok = self._peek()

        if tok.type == TokenType.RETURN:
            return self._parse_return()
        if tok.type == TokenType.IF:
            return self._parse_if()
        if tok.type == TokenType.WHILE:
            return self._parse_while()
        if tok.type == TokenType.FOR:
            return self._parse_for()
        if tok.type == TokenType.BREAK:
            self._advance()
            self._match(TokenType.NEWLINE)
            return BreakStmt(line=tok.line, col=tok.column)
        if tok.type == TokenType.CONTINUE:
            self._advance()
            self._match(TokenType.NEWLINE)
            return ContinueStmt(line=tok.line, col=tok.column)
        if tok.type in (TokenType.NEWLINE, TokenType.DEDENT, TokenType.INDENT):
            self._advance()
            return None

        return self._parse_expr_or_assign()

    def _parse_return(self) -> ReturnStmt:
        tok = self._advance()
        value = None
        if not self._check(TokenType.NEWLINE) and not self._at_end():
            value = self._parse_expr()
        self._match(TokenType.NEWLINE)
        return ReturnStmt(value=value, line=tok.line, col=tok.column)

    def _parse_if(self) -> IfStmt:
        tok = self._expect(TokenType.IF)
        cond = self._parse_expr()
        self._expect(TokenType.COLON, "Expected ':' after if condition")
        self._skip_newlines()
        then_body = self._parse_block()

        elif_clauses: List[Tuple] = []
        else_body:    List[ASTNode] = []

        self._skip_newlines()
        while self._check(TokenType.ELIF):
            self._advance()
            ec = self._parse_expr()
            self._expect(TokenType.COLON)
            self._skip_newlines()
            eb = self._parse_block()
            elif_clauses.append((ec, eb))
            self._skip_newlines()

        if self._check(TokenType.ELSE):
            self._advance()
            self._expect(TokenType.COLON)
            self._skip_newlines()
            else_body = self._parse_block()

        return IfStmt(condition=cond, then_body=then_body,
                      elif_clauses=elif_clauses, else_body=else_body,
                      line=tok.line, col=tok.column)

    def _parse_while(self) -> WhileStmt:
        tok = self._expect(TokenType.WHILE)
        cond = self._parse_expr()
        self._expect(TokenType.COLON, "Expected ':' after while condition")
        self._skip_newlines()
        body = self._parse_block()
        return WhileStmt(condition=cond, body=body, line=tok.line, col=tok.column)

    def _parse_for(self) -> ForStmt:
        tok = self._expect(TokenType.FOR)
        # "for each X in Y" or "for X in Y"
        self._match(TokenType.EACH)
        var = self._expect(TokenType.IDENTIFIER, "Expected loop variable").value
        self._expect(TokenType.IN, "Expected 'in' in for loop")
        iterable = self._parse_expr()
        self._expect(TokenType.COLON, "Expected ':' after for loop header")
        self._skip_newlines()
        body = self._parse_block()
        return ForStmt(var=var, iterable=iterable, body=body, line=tok.line, col=tok.column)

    def _parse_expr_or_assign(self) -> ASTNode:
        """Parse assignment or expression statement."""
        expr = self._parse_expr()
        ASSIGN_OPS = {
            TokenType.ASSIGN, TokenType.PLUS_EQ, TokenType.MINUS_EQ,
            TokenType.STAR_EQ, TokenType.SLASH_EQ,
        }
        tok = self._peek()
        if tok.type in ASSIGN_OPS:
            op = self._advance().value
            rhs = self._parse_expr()
            self._match(TokenType.NEWLINE)
            return AssignStmt(target=expr, value=rhs, op=op,
                              line=expr.line, col=expr.col)
        self._match(TokenType.NEWLINE)
        return ExprStmt(expr=expr, line=expr.line, col=expr.col)

    # ─── Expressions (Pratt-style precedence) ────────────────────────────

    def _parse_expr(self) -> ASTNode:
        return self._parse_or()

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        while self._check(TokenType.OR):
            op = self._advance().value
            right = self._parse_and()
            left = BinaryExpr(op=op, left=left, right=right, line=left.line, col=left.col)
        return left

    def _parse_and(self) -> ASTNode:
        left = self._parse_not()
        while self._check(TokenType.AND):
            op = self._advance().value
            right = self._parse_not()
            left = BinaryExpr(op=op, left=left, right=right, line=left.line, col=left.col)
        return left

    def _parse_not(self) -> ASTNode:
        if self._check(TokenType.NOT):
            tok = self._advance()
            operand = self._parse_not()
            return UnaryExpr(op='not', operand=operand, line=tok.line, col=tok.column)
        return self._parse_comparison()

    def _parse_comparison(self) -> ASTNode:
        left = self._parse_additive()
        CMP = {TokenType.EQ, TokenType.NEQ, TokenType.LT,
               TokenType.GT, TokenType.LTE, TokenType.GTE}
        while self._check(*CMP):
            op = self._advance().value
            right = self._parse_additive()
            left = BinaryExpr(op=op, left=left, right=right, line=left.line, col=left.col)
        return left

    def _parse_additive(self) -> ASTNode:
        left = self._parse_multiplicative()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            op = self._advance().value
            right = self._parse_multiplicative()
            left = BinaryExpr(op=op, left=left, right=right, line=left.line, col=left.col)
        return left

    def _parse_multiplicative(self) -> ASTNode:
        left = self._parse_unary()
        while self._check(TokenType.STAR, TokenType.SLASH,
                           TokenType.PERCENT, TokenType.FLOOR_DIV):
            op = self._advance().value
            right = self._parse_unary()
            left = BinaryExpr(op=op, left=left, right=right, line=left.line, col=left.col)
        return left

    def _parse_unary(self) -> ASTNode:
        if self._check(TokenType.MINUS):
            tok = self._advance()
            return UnaryExpr(op='-', operand=self._parse_unary(),
                             line=tok.line, col=tok.column)
        return self._parse_postfix()

    def _parse_postfix(self) -> ASTNode:
        expr = self._parse_primary()
        while True:
            if self._check(TokenType.LPAREN):
                # Function call
                self._advance()
                args = []
                while not self._check(TokenType.RPAREN) and not self._at_end():
                    args.append(self._parse_expr())
                    if not self._match(TokenType.COMMA):
                        break
                self._expect(TokenType.RPAREN, "Expected ')' in call")
                name = expr.name if isinstance(expr, Identifier) else str(expr)
                expr = CallExpr(callee=name, args=args, line=expr.line, col=expr.col)
            elif self._check(TokenType.LBRACKET):
                # Index
                self._advance()
                idx = self._parse_expr()
                self._expect(TokenType.RBRACKET, "Expected ']'")
                expr = IndexExpr(obj=expr, index=idx, line=expr.line, col=expr.col)
            elif self._check(TokenType.DOT):
                self._advance()
                member = self._expect(TokenType.IDENTIFIER, "Expected member name").value
                expr = MemberExpr(obj=expr, member=member, line=expr.line, col=expr.col)
            else:
                break
        return expr

    def _parse_primary(self) -> ASTNode:
        tok = self._peek()

        if tok.type == TokenType.INTEGER:
            self._advance()
            return IntLiteral(value=int(tok.value), line=tok.line, col=tok.column)

        if tok.type == TokenType.FLOAT:
            self._advance()
            return FloatLiteral(value=float(tok.value), line=tok.line, col=tok.column)

        if tok.type in (TokenType.TRUE, TokenType.FALSE):
            self._advance()
            return BoolLiteral(value=(tok.value.lower() == 'true'), line=tok.line, col=tok.column)

        if tok.type == TokenType.NULL:
            self._advance()
            return NullLiteral(line=tok.line, col=tok.column)

        if tok.type == TokenType.STRING:
            self._advance()
            return Identifier(name=f'"{tok.value}"', line=tok.line, col=tok.column)

        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return Identifier(name=tok.value, line=tok.line, col=tok.column)

        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expr()
            self._expect(TokenType.RPAREN, "Expected ')'")
            return expr

        if tok.type == TokenType.LBRACKET:
            self._advance()
            elems = []
            while not self._check(TokenType.RBRACKET) and not self._at_end():
                elems.append(self._parse_expr())
                if not self._match(TokenType.COMMA):
                    break
            self._expect(TokenType.RBRACKET, "Expected ']'")
            return ArrayLiteral(elements=elems, line=tok.line, col=tok.column)

        if tok.type == TokenType.MINUS:
            self._advance()
            operand = self._parse_primary()
            return UnaryExpr(op='-', operand=operand, line=tok.line, col=tok.column)

        raise ParseError("Unexpected token in expression", tok)
