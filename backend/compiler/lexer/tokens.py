"""
AlgoFlow Lexer — Token Definitions
Supports a Python-like pseudocode language for algorithm description.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional


class TokenType(Enum):
    # ── Literals ─────────────────────────────────────────
    INTEGER     = auto()
    FLOAT       = auto()
    STRING      = auto()
    BOOLEAN     = auto()

    # ── Identifiers & Keywords ───────────────────────────
    IDENTIFIER  = auto()

    # Keywords
    FUNCTION    = auto()
    RETURN      = auto()
    IF          = auto()
    ELSE        = auto()
    ELIF        = auto()
    WHILE       = auto()
    FOR         = auto()
    IN          = auto()
    BREAK       = auto()
    CONTINUE    = auto()
    AND         = auto()
    OR          = auto()
    NOT         = auto()
    TRUE        = auto()
    FALSE       = auto()
    NULL        = auto()
    LET         = auto()
    EACH        = auto()

    # ── Operators ────────────────────────────────────────
    PLUS        = auto()   # +
    MINUS       = auto()   # -
    STAR        = auto()   # *
    SLASH       = auto()   # /
    PERCENT     = auto()   # %
    POWER       = auto()   # **
    FLOOR_DIV   = auto()   # //

    EQ          = auto()   # ==
    NEQ         = auto()   # !=
    LT          = auto()   # <
    GT          = auto()   # >
    LTE         = auto()   # <=
    GTE         = auto()   # >=

    ASSIGN      = auto()   # =
    PLUS_EQ     = auto()   # +=
    MINUS_EQ    = auto()   # -=
    STAR_EQ     = auto()   # *=
    SLASH_EQ    = auto()   # /=

    # ── Delimiters ───────────────────────────────────────
    LPAREN      = auto()   # (
    RPAREN      = auto()   # )
    LBRACKET    = auto()   # [
    RBRACKET    = auto()   # ]
    LBRACE      = auto()   # {
    RBRACE      = auto()   # }
    COMMA       = auto()   # ,
    DOT         = auto()   # .
    COLON       = auto()   # :
    SEMICOLON   = auto()   # ;
    ARROW       = auto()   # ->

    # ── Layout ───────────────────────────────────────────
    NEWLINE     = auto()
    INDENT      = auto()
    DEDENT      = auto()

    # ── Special ──────────────────────────────────────────
    COMMENT     = auto()   # // or #
    EOF         = auto()
    ERROR       = auto()


KEYWORDS: dict[str, TokenType] = {
    "function":  TokenType.FUNCTION,
    "func":      TokenType.FUNCTION,
    "def":       TokenType.FUNCTION,
    "return":    TokenType.RETURN,
    "if":        TokenType.IF,
    "else":      TokenType.ELSE,
    "elif":      TokenType.ELIF,
    "while":     TokenType.WHILE,
    "for":       TokenType.FOR,
    "in":        TokenType.IN,
    "break":     TokenType.BREAK,
    "continue":  TokenType.CONTINUE,
    "and":       TokenType.AND,
    "or":        TokenType.OR,
    "not":       TokenType.NOT,
    "true":      TokenType.TRUE,
    "false":     TokenType.FALSE,
    "null":      TokenType.NULL,
    "None":      TokenType.NULL,
    "True":      TokenType.TRUE,
    "False":     TokenType.FALSE,
    "let":       TokenType.LET,
    "each":      TokenType.EACH,
}


@dataclass
class Token:
    type:    TokenType
    value:   str
    line:    int
    column:  int
    lexeme:  Optional[str] = None   # raw source text

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}:{self.column})"
