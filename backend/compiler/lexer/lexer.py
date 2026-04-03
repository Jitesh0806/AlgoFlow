"""
AlgoFlow Lexer — Scans pseudocode into a token stream.

Handles Python-style indentation (INDENT/DEDENT), multi-char operators,
keywords, identifiers, integer/float literals, and comments.
"""

from __future__ import annotations
from typing import List
from .tokens import Token, TokenType, KEYWORDS


class LexerError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"LexerError at {line}:{col} — {msg}")
        self.line = line
        self.col = col


class Lexer:
    """
    Hand-written lexer implementing the AlgoFlow scanning rules.

    Indentation model (Python-inspired):
      - Tracks indent stack; emits INDENT on increase, DEDENT(s) on decrease.
      - Physical newlines are emitted as NEWLINE after non-blank, non-comment lines.
    """

    def __init__(self, source: str):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.col    = 1
        self.tokens: List[Token] = []
        self._indent_stack: List[int] = [0]
        self._at_line_start = True

    # ─── Public API ──────────────────────────────────────────────────────────

    def tokenize(self) -> List[Token]:
        while not self._at_end():
            self._scan_token()
        # Flush remaining DEDENTs
        while self._indent_stack[-1] > 0:
            self._indent_stack.pop()
            self._emit(TokenType.DEDENT, "DEDENT")
        self._emit(TokenType.EOF, "")
        return self.tokens

    # ─── Core Scanner ────────────────────────────────────────────────────────

    def _scan_token(self):
        if self._at_line_start:
            self._handle_indent()

        c = self._peek()

        # Skip spaces/tabs (NOT newlines — those handled by _handle_indent)
        if c in (' ', '\t'):
            self._advance()
            return

        # Newline
        if c == '\n':
            self._advance()
            if self.tokens and self.tokens[-1].type not in (
                TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT,
                TokenType.COLON, TokenType.EOF
            ):
                self._emit(TokenType.NEWLINE, "\\n")
            self.line += 1
            self.col   = 1
            self._at_line_start = True
            return

        # Windows line ending
        if c == '\r':
            self._advance()
            return

        # Comments  // or #
        if c == '/' and self._peek_next() == '/':
            while not self._at_end() and self._peek() != '\n':
                self._advance()
            return
        if c == '#':
            while not self._at_end() and self._peek() != '\n':
                self._advance()
            return

        # String literals
        if c in ('"', "'"):
            self._string(c)
            return

        # Numbers
        if c.isdigit():
            self._number()
            return

        # Identifiers / keywords
        if c.isalpha() or c == '_':
            self._identifier()
            return

        # Operators & punctuation
        self._operator()

    # ─── Indentation Handling ─────────────────────────────────────────────

    def _handle_indent(self):
        """Count leading spaces, emit INDENT/DEDENT tokens."""
        spaces = 0
        save_pos = self.pos
        save_col = self.col

        while not self._at_end() and self._peek() in (' ', '\t'):
            if self._peek() == '\t':
                spaces += 4
            else:
                spaces += 1
            self._advance()

        # Blank line or comment-only line — skip indentation logic
        if self._at_end() or self._peek() == '\n' or (
            self._peek() == '/' and self._peek_next() == '/'
        ) or self._peek() == '#':
            return

        self._at_line_start = False
        current = self._indent_stack[-1]

        if spaces > current:
            self._indent_stack.append(spaces)
            self._emit(TokenType.INDENT, "INDENT")
        elif spaces < current:
            while self._indent_stack[-1] > spaces:
                self._indent_stack.pop()
                self._emit(TokenType.DEDENT, "DEDENT")

    # ─── Token Scanners ───────────────────────────────────────────────────

    def _string(self, quote: str):
        start = self.col
        self._advance()  # opening quote
        buf = []
        while not self._at_end() and self._peek() != quote:
            ch = self._advance()
            if ch == '\\':
                esc = self._advance()
                buf.append({'n': '\n', 't': '\t', '\\': '\\'}.get(esc, esc))
            else:
                buf.append(ch)
        if self._at_end():
            raise LexerError("Unterminated string", self.line, start)
        self._advance()  # closing quote
        self._emit(TokenType.STRING, ''.join(buf))

    def _number(self):
        buf = []
        while not self._at_end() and self._peek().isdigit():
            buf.append(self._advance())
        if not self._at_end() and self._peek() == '.' and self._peek_next().isdigit():
            buf.append(self._advance())  # '.'
            while not self._at_end() and self._peek().isdigit():
                buf.append(self._advance())
            self._emit(TokenType.FLOAT, ''.join(buf))
        else:
            self._emit(TokenType.INTEGER, ''.join(buf))

    def _identifier(self):
        buf = []
        while not self._at_end() and (self._peek().isalnum() or self._peek() == '_'):
            buf.append(self._advance())
        word = ''.join(buf)
        tok_type = KEYWORDS.get(word, TokenType.IDENTIFIER)
        self._emit(tok_type, word)

    def _operator(self):
        c = self._advance()
        col = self.col - 1

        two = c + (self._peek() if not self._at_end() else '')

        TWO_CHAR = {
            '==': TokenType.EQ,     '!=': TokenType.NEQ,
            '<=': TokenType.LTE,    '>=': TokenType.GTE,
            '+=': TokenType.PLUS_EQ, '-=': TokenType.MINUS_EQ,
            '*=': TokenType.STAR_EQ, '/=': TokenType.SLASH_EQ,
            '**': TokenType.POWER,  '//': None,   # handled as comment above
            '->': TokenType.ARROW,
        }

        if two in TWO_CHAR and TWO_CHAR[two] is not None:
            self._advance()
            self._emit(TWO_CHAR[two], two)
            return

        ONE_CHAR = {
            '+': TokenType.PLUS,    '-': TokenType.MINUS,
            '*': TokenType.STAR,    '/': TokenType.SLASH,
            '%': TokenType.PERCENT, '=': TokenType.ASSIGN,
            '<': TokenType.LT,      '>': TokenType.GT,
            '(': TokenType.LPAREN,  ')': TokenType.RPAREN,
            '[': TokenType.LBRACKET,']': TokenType.RBRACKET,
            '{': TokenType.LBRACE,  '}': TokenType.RBRACE,
            ',': TokenType.COMMA,   '.': TokenType.DOT,
            ':': TokenType.COLON,   ';': TokenType.SEMICOLON,
        }
        if c in ONE_CHAR:
            self._emit(ONE_CHAR[c], c)
            return

        raise LexerError(f"Unexpected character: {c!r}", self.line, col)

    # ─── Helpers ──────────────────────────────────────────────────────────

    def _peek(self) -> str:
        if self._at_end():
            return '\0'
        return self.source[self.pos]

    def _peek_next(self) -> str:
        if self.pos + 1 >= len(self.source):
            return '\0'
        return self.source[self.pos + 1]

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        self.col += 1
        return ch

    def _at_end(self) -> bool:
        return self.pos >= len(self.source)

    def _emit(self, type_: TokenType, value: str):
        self.tokens.append(Token(type_, value, self.line, self.col))
