from typing import List
from .tokens import Token, TokenType
from .diagnostics import Diagnostic, CompilerException, extract_snippet


class Lexer:
    KEYWORDS = {
        "model": TokenType.MODEL,
        "scenario": TokenType.SCENARIO,
        "for": TokenType.FOR,
        "in": TokenType.IN,
        "to": TokenType.TO,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "output": TokenType.OUTPUT,
        "and": TokenType.AND,
        "or": TokenType.OR,
        "not": TokenType.NOT,
    }

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []

    def current_char(self) -> str:
        if self.pos >= self.length:
            return "\0"
        return self.source[self.pos]

    def peek_char(self, offset: int = 1) -> str:
        target = self.pos + offset
        if target >= self.length:
            return "\0"
        return self.source[target]

    def advance(self) -> str:
        ch = self.current_char()
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.current_char() == expected:
            self.advance()
            return True
        return False

    def error(self, message: str, start_col: int, length: int = 1, suggestion: str = None):
        snippet = extract_snippet(self.source, self.line, start_col, length)
        diag = Diagnostic(
            phase="Lexer",
            message=message,
            line=self.line,
            column=start_col,
            length=length,
            severity="error",
            suggestion=suggestion,
            snippet=snippet
        )
        raise CompilerException(diag)

    def tokenize(self) -> List[Token]:
        self.tokens = []
        while self.pos < self.length:
            ch = self.current_char()

            # Whitespace
            if ch in " \t\r\n":
                self.advance()
                continue

            start_col = self.column

            # Comments
            if ch == "/" and self.peek_char() == "/":
                self.advance()
                self.advance()
                while self.current_char() not in ("\n", "\0"):
                    self.advance()
                continue

            if ch == "#":
                self.advance()
                while self.current_char() not in ("\n", "\0"):
                    self.advance()
                continue

            if ch == "/" and self.peek_char() == "*":
                self.advance()
                self.advance()
                start_line = self.line
                closed = False
                while self.current_char() != "\0":
                    if self.current_char() == "*" and self.peek_char() == "/":
                        self.advance()
                        self.advance()
                        closed = True
                        break
                    self.advance()
                if not closed:
                    self.line = start_line
                    self.error("Unterminated multi-line comment '/* ... */'", start_col, suggestion="Add '*/' to close the comment")
                continue

            # Numbers
            if ch.isdigit():
                self.tokens.append(self.lex_number(start_col))
                continue

            # Strings
            if ch == '"':
                self.tokens.append(self.lex_string(start_col))
                continue

            # Identifiers & Keywords
            if ch.isalpha() or ch == "_":
                self.tokens.append(self.lex_identifier(start_col))
                continue

            # Multi-character & Single-character operators
            if ch == "=":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.EQ, "==", self.line, start_col, 2))
                else:
                    self.tokens.append(Token(TokenType.ASSIGN, "=", self.line, start_col, 1))
                continue

            if ch == "!":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.NEQ, "!=", self.line, start_col, 2))
                else:
                    self.error("Unexpected character '!'", start_col, 1, suggestion="Did you mean '!=' or keyword 'not'?")
                continue

            if ch == "<":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.LTE, "<=", self.line, start_col, 2))
                else:
                    self.tokens.append(Token(TokenType.LT, "<", self.line, start_col, 1))
                continue

            if ch == ">":
                self.advance()
                if self.match("="):
                    self.tokens.append(Token(TokenType.GTE, ">=", self.line, start_col, 2))
                else:
                    self.tokens.append(Token(TokenType.GT, ">", self.line, start_col, 1))
                continue

            if ch == "+":
                self.advance()
                self.tokens.append(Token(TokenType.PLUS, "+", self.line, start_col, 1))
                continue

            if ch == "-":
                self.advance()
                self.tokens.append(Token(TokenType.MINUS, "-", self.line, start_col, 1))
                continue

            if ch == "*":
                self.advance()
                self.tokens.append(Token(TokenType.STAR, "*", self.line, start_col, 1))
                continue

            if ch == "/":
                self.advance()
                self.tokens.append(Token(TokenType.SLASH, "/", self.line, start_col, 1))
                continue

            if ch == "%":
                self.advance()
                self.tokens.append(Token(TokenType.PERCENT, "%", self.line, start_col, 1))
                continue

            if ch == "^":
                self.advance()
                self.tokens.append(Token(TokenType.CARET, "^", self.line, start_col, 1))
                continue

            if ch == "(":
                self.advance()
                self.tokens.append(Token(TokenType.LPAREN, "(", self.line, start_col, 1))
                continue

            if ch == ")":
                self.advance()
                self.tokens.append(Token(TokenType.RPAREN, ")", self.line, start_col, 1))
                continue

            if ch == "{":
                self.advance()
                self.tokens.append(Token(TokenType.LBRACE, "{", self.line, start_col, 1))
                continue

            if ch == "}":
                self.advance()
                self.tokens.append(Token(TokenType.RBRACE, "}", self.line, start_col, 1))
                continue

            if ch == ",":
                self.advance()
                self.tokens.append(Token(TokenType.COMMA, ",", self.line, start_col, 1))
                continue

            # Unrecognized character
            illegal = self.advance()
            self.error(f"Unexpected character '{illegal}' in source code", start_col, 1, suggestion="Remove this invalid character")

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column, 0))
        return self.tokens

    def lex_number(self, start_col: int) -> Token:
        num_str = ""
        has_dot = False

        while self.current_char().isdigit() or (self.current_char() == "." and not has_dot):
            if self.current_char() == ".":
                # Ensure it's not a range like 1..10
                if self.peek_char() == ".":
                    break
                has_dot = True
            num_str += self.advance()

        # Scientific notation e.g. 1e5, 2.5e-3
        if self.current_char() in ("e", "E"):
            next_ch = self.peek_char()
            if next_ch.isdigit() or next_ch in ("+", "-"):
                num_str += self.advance()
                num_str += self.advance()
                while self.current_char().isdigit():
                    num_str += self.advance()

        val = float(num_str) if has_dot or "e" in num_str.lower() else int(num_str)
        return Token(TokenType.NUMBER, val, self.line, start_col, len(num_str))

    def lex_string(self, start_col: int) -> Token:
        self.advance()  # consume opening "
        content = ""
        while self.current_char() != '"' and self.current_char() != "\0":
            if self.current_char() == "\\":
                self.advance()
                esc = self.current_char()
                if esc == "n":
                    content += "\n"
                elif esc == "t":
                    content += "\t"
                elif esc == '"':
                    content += '"'
                elif esc == "\\":
                    content += "\\"
                else:
                    content += esc
                self.advance()
            else:
                content += self.advance()

        if self.current_char() != '"':
            self.error("Unterminated string literal", start_col, len(content) + 1, suggestion='Add closing double quote "')

        self.advance()  # consume closing "
        return Token(TokenType.STRING, content, self.line, start_col, len(content) + 2)

    def lex_identifier(self, start_col: int) -> Token:
        ident = ""
        while self.current_char().isalnum() or self.current_char() == "_":
            ident += self.advance()

        tok_type = self.KEYWORDS.get(ident.lower(), TokenType.IDENTIFIER)
        # Note: if it's a keyword like 'model', the value is the canonical lowercase or keyword name
        return Token(tok_type, ident, self.line, start_col, len(ident))
