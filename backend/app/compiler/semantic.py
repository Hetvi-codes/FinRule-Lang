from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from .ast_nodes import (
    ProgramNode, ModelNode, ScenarioNode, StatementNode,
    AssignNode, ForLoopNode, IfNode, OutputNode,
    ExprNode, NumberLiteralNode, StringLiteralNode, IdentifierNode,
    BinaryOpNode, UnaryOpNode, FunctionCallNode
)
from .diagnostics import Diagnostic, CompilerException, extract_snippet


@dataclass
class Symbol:
    name: str
    symbol_type: str  # "number", "string", "iterator", "function", "any"
    scope_name: str
    line_defined: int
    column_defined: int

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.symbol_type,
            "scope": self.scope_name,
            "line": self.line_defined,
            "column": self.column_defined
        }


class Scope:
    def __init__(self, name: str, parent: Optional["Scope"] = None):
        self.name = name
        self.parent = parent
        self.symbols: Dict[str, Symbol] = {}

    def define(self, symbol: Symbol):
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def get_all_symbols(self) -> List[Symbol]:
        syms = list(self.symbols.values())
        if self.parent:
            syms.extend(self.parent.get_all_symbols())
        return syms


class SemanticAnalyzer:
    BUILTIN_FUNCTIONS = {
        "growth": {"min_args": 3, "max_args": 3, "desc": "GROWTH(base, rate, period)"},
        "compound": {"min_args": 3, "max_args": 3, "desc": "COMPOUND(principal, rate, periods)"},
        "pmt": {"min_args": 3, "max_args": 4, "desc": "PMT(rate, nper, pv, [fv])"},
        "fv": {"min_args": 3, "max_args": 4, "desc": "FV(rate, nper, pmt, [pv])"},
        "npv": {"min_args": 2, "max_args": 50, "desc": "NPV(discount_rate, value1, value2, ...)"},
        "round": {"min_args": 1, "max_args": 2, "desc": "ROUND(value, [decimals])"},
        "min": {"min_args": 2, "max_args": 20, "desc": "MIN(val1, val2, ...)"},
        "max": {"min_args": 2, "max_args": 20, "desc": "MAX(val1, val2, ...)"},
        "abs": {"min_args": 1, "max_args": 1, "desc": "ABS(value)"},
    }

    def __init__(self, source: str = ""):
        self.source = source
        self.global_scope = Scope("global")
        self.current_scope = self.global_scope
        self.diagnostics: List[Diagnostic] = []
        self.symbol_history: List[Symbol] = []

        # Register builtins in global scope
        for fn_name in self.BUILTIN_FUNCTIONS:
            sym = Symbol(fn_name, "function", "builtin", 0, 0)
            self.global_scope.define(sym)

    def analyze(self, program: ProgramNode) -> List[Symbol]:
        self.diagnostics = []
        self.symbol_history = []

        for model in program.models:
            self.analyze_model(model)

        for scenario in program.scenarios:
            self.analyze_scenario(scenario)

        # If any fatal error diagnostics exist, raise CompilerException
        errors = [d for d in self.diagnostics if d.severity == "error"]
        if errors:
            raise CompilerException(errors[0])

        return self.symbol_history

    def analyze_model(self, model: ModelNode):
        model_scope = Scope(f"model:{model.name}", self.current_scope)
        self.current_scope = model_scope

        for stmt in model.body:
            self.analyze_statement(stmt)

        self.current_scope = self.current_scope.parent

    def analyze_scenario(self, scenario: ScenarioNode):
        scenario_scope = Scope(f"scenario:{scenario.name}", self.current_scope)
        self.current_scope = scenario_scope

        for stmt in scenario.body:
            self.analyze_statement(stmt)

        self.current_scope = self.current_scope.parent

    def analyze_statement(self, stmt: StatementNode):
        if isinstance(stmt, AssignNode):
            # Check expression first
            expr_type = self.analyze_expression(stmt.expr)
            # Define symbol
            sym = Symbol(
                name=stmt.target,
                symbol_type=expr_type or "number",
                scope_name=self.current_scope.name,
                line_defined=stmt.line,
                column_defined=stmt.column
            )
            self.current_scope.define(sym)
            self.symbol_history.append(sym)

        elif isinstance(stmt, ForLoopNode):
            # Check loop bounds
            start_type = self.analyze_expression(stmt.start_expr)
            end_type = self.analyze_expression(stmt.end_expr)

            # Static check if start > end on literals
            if isinstance(stmt.start_expr, NumberLiteralNode) and isinstance(stmt.end_expr, NumberLiteralNode):
                if stmt.start_expr.value > stmt.end_expr.value:
                    self.add_diagnostic(
                        "Loop start value is greater than end value",
                        stmt.line,
                        stmt.column,
                        severity="warning",
                        suggestion=f"Loop from {stmt.start_expr.value} to {stmt.end_expr.value} will not execute."
                    )

            loop_scope = Scope(f"loop:{stmt.iterator}", self.current_scope)
            self.current_scope = loop_scope

            iter_sym = Symbol(
                name=stmt.iterator,
                symbol_type="iterator",
                scope_name=self.current_scope.name,
                line_defined=stmt.line,
                column_defined=stmt.column
            )
            self.current_scope.define(iter_sym)
            self.symbol_history.append(iter_sym)

            for inner_stmt in stmt.body:
                self.analyze_statement(inner_stmt)

            self.current_scope = self.current_scope.parent

        elif isinstance(stmt, IfNode):
            self.analyze_expression(stmt.condition)
            for inner_stmt in stmt.then_body:
                self.analyze_statement(inner_stmt)
            if stmt.else_body:
                for inner_stmt in stmt.else_body:
                    self.analyze_statement(inner_stmt)

        elif isinstance(stmt, OutputNode):
            for var_name in stmt.variables:
                sym = self.current_scope.lookup(var_name)
                if not sym:
                    self.add_diagnostic(
                        f"Variable '{var_name}' referenced in output is not declared or initialized.",
                        stmt.line,
                        stmt.column,
                        severity="error",
                        suggestion=f"Define '{var_name} = ...' before outputting it."
                    )

    def analyze_expression(self, expr: ExprNode) -> str:
        if isinstance(expr, NumberLiteralNode):
            return "number"

        if isinstance(expr, StringLiteralNode):
            return "string"

        if isinstance(expr, IdentifierNode):
            sym = self.current_scope.lookup(expr.name)
            if not sym:
                self.add_diagnostic(
                    f"Undefined variable '{expr.name}'",
                    expr.line,
                    expr.column,
                    length=len(expr.name),
                    severity="error",
                    suggestion=f"Make sure to define and assign '{expr.name}' before using it."
                )
                return "any"
            return sym.symbol_type

        if isinstance(expr, BinaryOpNode):
            left_type = self.analyze_expression(expr.left)
            right_type = self.analyze_expression(expr.right)

            # Static division by zero check
            if expr.op == "/" and isinstance(expr.right, NumberLiteralNode) and expr.right.value == 0:
                self.add_diagnostic(
                    "Division by constant zero detected",
                    expr.line,
                    expr.column,
                    severity="error",
                    suggestion="Denominator cannot be zero in financial calculations."
                )

            return "number"

        if isinstance(expr, UnaryOpNode):
            return self.analyze_expression(expr.operand)

        if isinstance(expr, FunctionCallNode):
            fn_lower = expr.name.lower()
            if fn_lower not in self.BUILTIN_FUNCTIONS:
                self.add_diagnostic(
                    f"Unknown financial function '{expr.name}'",
                    expr.line,
                    expr.column,
                    length=len(expr.name),
                    severity="error",
                    suggestion=f"Supported functions are: {', '.join(k.upper() for k in self.BUILTIN_FUNCTIONS.keys())}"
                )
            else:
                meta = self.BUILTIN_FUNCTIONS[fn_lower]
                arg_count = len(expr.args)
                if arg_count < meta["min_args"] or arg_count > meta["max_args"]:
                    self.add_diagnostic(
                        f"Function '{expr.name}' expects between {meta['min_args']} and {meta['max_args']} arguments, but got {arg_count}.",
                        expr.line,
                        expr.column,
                        severity="error",
                        suggestion=f"Usage: {meta['desc']}"
                    )

            for arg in expr.args:
                self.analyze_expression(arg)

            return "number"

        return "any"

    def add_diagnostic(self, message: str, line: int, column: int, length: int = 1, severity: str = "error", suggestion: str = None):
        snippet = extract_snippet(self.source, line, column, length)
        diag = Diagnostic(
            phase="Semantic",
            message=message,
            line=line,
            column=column,
            length=length,
            severity=severity,
            suggestion=suggestion,
            snippet=snippet
        )
        self.diagnostics.append(diag)
