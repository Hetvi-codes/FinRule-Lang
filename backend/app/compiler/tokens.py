from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Keywords
    MODEL = "MODEL"
    SCENARIO = "SCENARIO"
    FOR = "FOR"
    IN = "IN"
    TO = "TO"
    IF = "IF"
    ELSE = "ELSE"
    OUTPUT = "OUTPUT"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    # Literals & Identifiers
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    STRING = "STRING"

    # Operators
    ASSIGN = "="
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    PERCENT = "%"
    CARET = "^"
    
    # Comparisons
    EQ = "=="
    NEQ = "!="
    LT = "<"
    LTE = "<="
    GT = ">"
    GTE = ">="

    # Delimiters
    LPAREN = "("
    RPAREN = ")"
    LBRACE = "{"
    RBRACE = "}"
    COMMA = ","
    
    # Special
    EOF = "EOF"
    NEWLINE = "NEWLINE"


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    column: int
    length: int = 1

    def to_dict(self) -> dict:
        return {
            "type": self.type.value if hasattr(self.type, "value") else str(self.type),
            "value": self.value,
            "line": self.line,
            "column": self.column,
            "length": self.length
        }

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:C{self.column})"
