from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Diagnostic:
    phase: str          # "Lexer", "Parser", "Semantic", "Runtime"
    message: str
    line: int
    column: int
    length: int = 1
    severity: str = "error"  # "error", "warning", "info"
    suggestion: Optional[str] = None
    snippet: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "length": self.length,
            "severity": self.severity,
            "suggestion": self.suggestion,
            "snippet": self.snippet
        }


class CompilerException(Exception):
    def __init__(self, diagnostic: Diagnostic):
        super().__init__(f"[{diagnostic.phase} Error] L{diagnostic.line}:C{diagnostic.column} - {diagnostic.message}")
        self.diagnostic = diagnostic


def extract_snippet(source: str, line: int, column: int, length: int = 1) -> str:
    lines = source.splitlines()
    if 1 <= line <= len(lines):
        src_line = lines[line - 1]
        col_pos = max(0, column - 1)
        pointer = " " * col_pos + "^" * max(1, length)
        return f"{src_line}\n{pointer}"
    return ""
