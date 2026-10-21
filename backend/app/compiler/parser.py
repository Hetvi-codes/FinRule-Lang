from typing import List, Optional
from .tokens import Token, TokenType
from .diagnostics import Diagnostic, CompilerException, extract_snippet
from .ast_nodes import (
    ProgramNode, ModelNode, ScenarioNode, StatementNode,
    AssignNode, ForLoopNode, IfNode, OutputNode,
    ExprNode, NumberLiteralNode, StringLiteralNode, IdentifierNode,
    BinaryOpNode, UnaryOpNode, FunctionCallNode
)


class Parser:
    def __init__(self, tokens: List[Token], source: str = ""):
        self.tokens = tokens
        self.source = source
        self.pos = 0

    def current_token(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def peek_token(self, offset: int = 1) -> Token:
        target = self.pos + offset
        if target >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[target]

    def advance(self) -> Token:
        tok = self.current_token()
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def check(self, token_type: TokenType) -> bool:
        return self.current_token().type == token_type

    def match(self, *token_types: TokenType) -> bool:
        for tt in token_types:
            if self.check(tt):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, error_message: str, suggestion: str = None) -> Token:
        if self.check(token_type):
            return self.advance()
        tok = self.current_token()
        self.error(error_message, tok, suggestion)

    def error(self, message: str, token: Optional[Token] = None, suggestion: str = None):
        tok = token or self.current_token()
        snippet = extract_snippet(self.source, tok.line, tok.column, max(1, tok.length))
        diag = Diagnostic(
            phase="Parser",
            message=message,
            line=tok.line,
            column=tok.column,
            length=max(1, tok.length),
            severity="error",
            suggestion=suggestion,
            snippet=snippet
        )
        raise CompilerException(diag)

    def parse(self) -> ProgramNode:
        models: List[ModelNode] = []
        scenarios: List[ScenarioNode] = []
        loose_statements: List[StatementNode] = []

        first_tok = self.current_token()

        while not self.check(TokenType.EOF):
            if self.check(TokenType.MODEL):
                models.append(self.parse_model())
            elif self.check(TokenType.SCENARIO):
                scenarios.append(self.parse_scenario())
            else:
                # Support implicit model if user writes statements directly without 'model "..." { ... }'
                loose_statements.append(self.parse_statement())

        # If user wrote statements directly without model block, wrap in a default ModelNode
        if loose_statements and not models:
            models.append(ModelNode(
                name="Default Financial Model",
                body=loose_statements,
                line=first_tok.line,
                column=first_tok.column
            ))
        elif loose_statements and models:
            # Append loose statements to the first model
            models[0].body.extend(loose_statements)

        return ProgramNode(
            models=models,
            scenarios=scenarios,
            line=first_tok.line,
            column=first_tok.column
        )

    def parse_model(self) -> ModelNode:
        mod_tok = self.consume(TokenType.MODEL, "Expected 'model' keyword")
        name_tok = self.consume(TokenType.STRING, "Expected string name for model, e.g., model \"SaaS Growth Model\"", suggestion='Add a model name in double quotes, e.g. "My Model"')
        self.consume(TokenType.LBRACE, "Expected '{' to start model block", suggestion="Add '{' after the model name")

        body: List[StatementNode] = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            body.append(self.parse_statement())

        self.consume(TokenType.RBRACE, "Expected '}' to close model block", suggestion="Add '}' to close the model block")
        return ModelNode(name=name_tok.value, body=body, line=mod_tok.line, column=mod_tok.column)

    def parse_scenario(self) -> ScenarioNode:
        scen_tok = self.consume(TokenType.SCENARIO, "Expected 'scenario' keyword")
        name_tok = self.consume(TokenType.STRING, "Expected string name for scenario, e.g., scenario \"Aggressive Growth\"", suggestion='Add scenario name in double quotes, e.g. "Bull Case"')
        self.consume(TokenType.LBRACE, "Expected '{' to start scenario block", suggestion="Add '{' after the scenario name")

        body: List[StatementNode] = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            body.append(self.parse_statement())

        self.consume(TokenType.RBRACE, "Expected '}' to close scenario block", suggestion="Add '}' to close the scenario block")
        return ScenarioNode(name=name_tok.value, body=body, line=scen_tok.line, column=scen_tok.column)

    def parse_statement(self) -> StatementNode:
        if self.check(TokenType.FOR):
            return self.parse_for_loop()
        elif self.check(TokenType.IF):
            return self.parse_if()
        elif self.check(TokenType.OUTPUT):
            return self.parse_output()
        elif self.check(TokenType.IDENTIFIER) and self.peek_token().type == TokenType.ASSIGN:
            return self.parse_assignment()
        else:
            tok = self.current_token()
            self.error(f"Unexpected token '{tok.value}' where a statement was expected", tok, suggestion="Expected assignment (x = 10), loop (for ...), condition (if ...), or output directive")

    def parse_assignment(self) -> AssignNode:
        ident_tok = self.consume(TokenType.IDENTIFIER, "Expected identifier for assignment")
        self.consume(TokenType.ASSIGN, "Expected '=' in assignment")
        expr = self.parse_expression()
        return AssignNode(target=ident_tok.value, expr=expr, line=ident_tok.line, column=ident_tok.column)

    def parse_for_loop(self) -> ForLoopNode:
        for_tok = self.consume(TokenType.FOR, "Expected 'for' keyword")
        iter_tok = self.consume(TokenType.IDENTIFIER, "Expected loop variable name after 'for'", suggestion="e.g. 'for month in 1 to 24'")
        self.consume(TokenType.IN, "Expected 'in' keyword after loop variable", suggestion="Add 'in'")
        start_expr = self.parse_expression()
        self.consume(TokenType.TO, "Expected 'to' keyword in loop range", suggestion="Add 'to' range boundary")
        end_expr = self.parse_expression()

        self.consume(TokenType.LBRACE, "Expected '{' to begin loop body", suggestion="Add '{'")
        body: List[StatementNode] = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            body.append(self.parse_statement())

        self.consume(TokenType.RBRACE, "Expected '}' to close loop body", suggestion="Add '}'")
        return ForLoopNode(
            iterator=iter_tok.value,
            start_expr=start_expr,
            end_expr=end_expr,
            body=body,
            line=for_tok.line,
            column=for_tok.column
        )

    def parse_if(self) -> IfNode:
        if_tok = self.consume(TokenType.IF, "Expected 'if' keyword")
        self.consume(TokenType.LPAREN, "Expected '(' after 'if'", suggestion="Enclose condition in parentheses, e.g. if (revenue > 1000)")
        cond = self.parse_expression()
        self.consume(TokenType.RPAREN, "Expected ')' after if condition", suggestion="Add ')'")

        self.consume(TokenType.LBRACE, "Expected '{' to begin if branch", suggestion="Add '{'")
        then_body: List[StatementNode] = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            then_body.append(self.parse_statement())
        self.consume(TokenType.RBRACE, "Expected '}' to close if branch", suggestion="Add '}'")

        else_body = None
        if self.match(TokenType.ELSE):
            self.consume(TokenType.LBRACE, "Expected '{' to begin else branch", suggestion="Add '{'")
            else_body = []
            while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
                else_body.append(self.parse_statement())
            self.consume(TokenType.RBRACE, "Expected '}' to close else branch", suggestion="Add '}'")

        return IfNode(condition=cond, then_body=then_body, else_body=else_body, line=if_tok.line, column=if_tok.column)

    def parse_output(self) -> OutputNode:
        out_tok = self.consume(TokenType.OUTPUT, "Expected 'output' keyword")
        variables: List[str] = []
        
        first_var = self.consume(TokenType.IDENTIFIER, "Expected variable name after 'output'", suggestion="e.g. output month, revenue, profit")
        variables.append(first_var.value)

        while self.match(TokenType.COMMA):
            var_tok = self.consume(TokenType.IDENTIFIER, "Expected variable name after comma in output list")
            variables.append(var_tok.value)

        return OutputNode(variables=variables, line=out_tok.line, column=out_tok.column)

    # --- Expression Parser (Operator Precedence) ---

    def parse_expression(self) -> ExprNode:
        return self.parse_logic_or()

    def parse_logic_or(self) -> ExprNode:
        expr = self.parse_logic_and()
        while self.match(TokenType.OR):
            op = "or"
            right = self.parse_logic_and()
            expr = BinaryOpNode(op=op, left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def parse_logic_and(self) -> ExprNode:
        expr = self.parse_equality()
        while self.match(TokenType.AND):
            op = "and"
            right = self.parse_equality()
            expr = BinaryOpNode(op=op, left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def parse_equality(self) -> ExprNode:
        expr = self.parse_relational()
        while self.check(TokenType.EQ) or self.check(TokenType.NEQ):
            op_tok = self.advance()
            right = self.parse_relational()
            expr = BinaryOpNode(op=op_tok.value, left=expr, right=right, line=op_tok.line, column=op_tok.column)
        return expr

    def parse_relational(self) -> ExprNode:
        expr = self.parse_term()
        while self.check(TokenType.LT) or self.check(TokenType.LTE) or self.check(TokenType.GT) or self.check(TokenType.GTE):
            op_tok = self.advance()
            right = self.parse_term()
            expr = BinaryOpNode(op=op_tok.value, left=expr, right=right, line=op_tok.line, column=op_tok.column)
        return expr

    def parse_term(self) -> ExprNode:
        expr = self.parse_factor()
        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            op_tok = self.advance()
            right = self.parse_factor()
            expr = BinaryOpNode(op=op_tok.value, left=expr, right=right, line=op_tok.line, column=op_tok.column)
        return expr

    def parse_factor(self) -> ExprNode:
        expr = self.parse_power()
        while self.check(TokenType.STAR) or self.check(TokenType.SLASH) or self.check(TokenType.PERCENT):
            op_tok = self.advance()
            right = self.parse_power()
            expr = BinaryOpNode(op=op_tok.value, left=expr, right=right, line=op_tok.line, column=op_tok.column)
        return expr

    def parse_power(self) -> ExprNode:
        expr = self.parse_unary()
        if self.match(TokenType.CARET):
            # Power is right-associative (2 ^ 3 ^ 2 = 2 ^ (3 ^ 2))
            right = self.parse_power()
            expr = BinaryOpNode(op="^", left=expr, right=right, line=expr.line, column=expr.column)
        return expr

    def parse_unary(self) -> ExprNode:
        if self.check(TokenType.MINUS) or self.check(TokenType.PLUS) or self.check(TokenType.NOT):
            op_tok = self.advance()
            operand = self.parse_unary()
            return UnaryOpNode(op=op_tok.value, operand=operand, line=op_tok.line, column=op_tok.column)
        return self.parse_primary()

    def parse_primary(self) -> ExprNode:
        tok = self.current_token()

        if self.match(TokenType.NUMBER):
            return NumberLiteralNode(value=tok.value, line=tok.line, column=tok.column)

        if self.match(TokenType.STRING):
            return StringLiteralNode(value=tok.value, line=tok.line, column=tok.column)

        if self.match(TokenType.IDENTIFIER):
            # Check if this is a function call: identifier '('
            if self.match(TokenType.LPAREN):
                args: List[ExprNode] = []
                if not self.check(TokenType.RPAREN):
                    args.append(self.parse_expression())
                    while self.match(TokenType.COMMA):
                        args.append(self.parse_expression())
                self.consume(TokenType.RPAREN, f"Expected ')' closing arguments of function '{tok.value}'", suggestion="Add ')'")
                return FunctionCallNode(name=tok.value, args=args, line=tok.line, column=tok.column)
            return IdentifierNode(name=tok.value, line=tok.line, column=tok.column)

        if self.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression", suggestion="Add ')'")
            return expr

        self.error(f"Unexpected token '{tok.value}' in expression", tok, suggestion="Expected number, variable name, or '(' expression ')'")
