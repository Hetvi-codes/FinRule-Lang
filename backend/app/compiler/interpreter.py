import time
from typing import Dict, List, Any, Optional
from .ast_nodes import (
    ProgramNode, ModelNode, ScenarioNode, StatementNode,
    AssignNode, ForLoopNode, IfNode, OutputNode,
    ExprNode, NumberLiteralNode, StringLiteralNode, IdentifierNode,
    BinaryOpNode, UnaryOpNode, FunctionCallNode
)
from .builtins import FINANCIAL_BUILTINS
from .diagnostics import Diagnostic, CompilerException, extract_snippet


class ExecutionEnvironment:
    def __init__(self, parent: Optional["ExecutionEnvironment"] = None):
        self.parent = parent
        self.values: Dict[str, Any] = {}

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name: str, value: Any):
        # If exists in parent or current, set accordingly
        if self.parent and self.parent.get(name) is not None:
            self.parent.set(name, value)
        else:
            self.values[name] = value

    def define(self, name: str, value: Any):
        self.values[name] = value


class Interpreter:
    def __init__(self, source: str = ""):
        self.source = source
        self.output_rows: List[Dict[str, Any]] = []
        self.output_columns: List[str] = []
        self.max_loop_iterations = 240  # safety threshold (20 years monthly)

    def execute_program(self, program: ProgramNode, selected_scenario_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the primary model and scenarios.
        Returns:
            {
                "model_name": str,
                "columns": List[str],
                "rows": List[Dict[str, Any]],
                "summaries": Dict[str, Any],
                "scenarios": Dict[str, { "columns": List[str], "rows": List[Dict[str, Any]], "summaries": Dict[str, Any] }]
            }
        """
        if not program.models:
            return {
                "model_name": "Empty Model",
                "columns": [],
                "rows": [],
                "summaries": {},
                "scenarios": {}
            }

        primary_model = program.models[0]

        # 1. Execute Base Model
        base_result = self.execute_model(primary_model, scenario_overrides=None)

        # 2. Execute all scenarios defined in program
        scenario_results = {}
        for scenario in program.scenarios:
            # Extract scenario assignment overrides
            overrides = self.extract_scenario_overrides(scenario)
            scen_res = self.execute_model(primary_model, scenario_overrides=overrides)
            scenario_results[scenario.name] = scen_res

        return {
            "model_name": primary_model.name,
            "columns": base_result["columns"],
            "rows": base_result["rows"],
            "summaries": base_result["summaries"],
            "scenarios": scenario_results
        }

    def extract_scenario_overrides(self, scenario: ScenarioNode) -> Dict[str, Any]:
        env = ExecutionEnvironment()
        for stmt in scenario.body:
            if isinstance(stmt, AssignNode):
                val = self.eval_expr(stmt.expr, env)
                env.define(stmt.target, val)
        return env.values

    def execute_model(self, model: ModelNode, scenario_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.output_rows = []
        self.output_columns = []
        env = ExecutionEnvironment()

        for stmt in model.body:
            if isinstance(stmt, AssignNode):
                # If this variable is in scenario overrides, use the overridden value
                if scenario_overrides and stmt.target in scenario_overrides:
                    val = scenario_overrides[stmt.target]
                else:
                    val = self.eval_expr(stmt.expr, env)
                env.define(stmt.target, val)
            else:
                self.exec_statement(stmt, env)

        summaries = self.calculate_summaries(self.output_rows, self.output_columns)

        return {
            "columns": self.output_columns,
            "rows": self.output_rows,
            "summaries": summaries
        }

    def exec_statement(self, stmt: StatementNode, env: ExecutionEnvironment):
        if isinstance(stmt, AssignNode):
            val = self.eval_expr(stmt.expr, env)
            env.set(stmt.target, val)

        elif isinstance(stmt, ForLoopNode):
            start_val = int(self.eval_expr(stmt.start_expr, env))
            end_val = int(self.eval_expr(stmt.end_expr, env))

            total_iters = end_val - start_val + 1
            if total_iters > self.max_loop_iterations:
                self.error(
                    f"Loop iteration count ({total_iters}) exceeds safety limit of {self.max_loop_iterations}.",
                    stmt.line,
                    stmt.column,
                    suggestion=f"Reduce loop range to at most {self.max_loop_iterations} periods."
                )

            for step in range(start_val, end_val + 1):
                loop_env = ExecutionEnvironment(parent=env)
                loop_env.define(stmt.iterator, step)

                for inner_stmt in stmt.body:
                    self.exec_statement(inner_stmt, loop_env)

        elif isinstance(stmt, IfNode):
            cond_val = self.eval_expr(stmt.condition, env)
            if bool(cond_val):
                for inner_stmt in stmt.then_body:
                    self.exec_statement(inner_stmt, env)
            elif stmt.else_body:
                for inner_stmt in stmt.else_body:
                    self.exec_statement(inner_stmt, env)

        elif isinstance(stmt, OutputNode):
            row_data = {}
            for var_name in stmt.variables:
                if var_name not in self.output_columns:
                    self.output_columns.append(var_name)
                val = env.get(var_name)
                # Format floats to 2 decimal places if clean
                if isinstance(val, float):
                    row_data[var_name] = round(val, 2)
                else:
                    row_data[var_name] = val
            self.output_rows.append(row_data)

    def eval_expr(self, expr: ExprNode, env: ExecutionEnvironment) -> Any:
        if isinstance(expr, NumberLiteralNode):
            return expr.value

        if isinstance(expr, StringLiteralNode):
            return expr.value

        if isinstance(expr, IdentifierNode):
            val = env.get(expr.name)
            if val is None:
                self.error(
                    f"Runtime error: Variable '{expr.name}' was not initialized before use.",
                    expr.line,
                    expr.column,
                    suggestion=f"Assign '{expr.name} = ...' prior to evaluating."
                )
            return val

        if isinstance(expr, BinaryOpNode):
            left_val = self.eval_expr(expr.left, env)
            right_val = self.eval_expr(expr.right, env)

            op = expr.op
            try:
                if op == "+": return left_val + right_val
                if op == "-": return left_val - right_val
                if op == "*": return left_val * right_val
                if op == "/":
                    if right_val == 0:
                        self.error("Division by zero in runtime expression.", expr.line, expr.column, suggestion="Ensure denominator is non-zero.")
                    return left_val / right_val
                if op == "%": return left_val % right_val
                if op == "^": return left_val ** right_val
                if op == "==": return left_val == right_val
                if op == "!=": return left_val != right_val
                if op == "<": return left_val < right_val
                if op == "<=": return left_val <= right_val
                if op == ">": return left_val > right_val
                if op == ">=": return left_val >= right_val
                if op == "and": return bool(left_val) and bool(right_val)
                if op == "or": return bool(left_val) or bool(right_val)
            except Exception as e:
                self.error(f"Arithmetic evaluation error: {str(e)}", expr.line, expr.column)

        if isinstance(expr, UnaryOpNode):
            operand_val = self.eval_expr(expr.operand, env)
            if expr.op == "-":
                return -operand_val
            if expr.op == "+":
                return +operand_val
            if expr.op == "not":
                return not bool(operand_val)

        if isinstance(expr, FunctionCallNode):
            fn_name = expr.name.lower()
            if fn_name not in FINANCIAL_BUILTINS:
                self.error(f"Unknown financial function '{expr.name}'", expr.line, expr.column)

            arg_vals = [self.eval_expr(arg, env) for arg in expr.args]
            try:
                fn = FINANCIAL_BUILTINS[fn_name]
                return fn(*arg_vals)
            except Exception as e:
                self.error(f"Error executing function '{expr.name}': {str(e)}", expr.line, expr.column)

        return 0

    def calculate_summaries(self, rows: List[Dict[str, Any]], columns: List[str]) -> Dict[str, Any]:
        if not rows:
            return {}

        summaries = {}
        for col in columns:
            vals = [r[col] for r in rows if col in r and isinstance(r[col], (int, float))]
            if not vals:
                continue

            total = sum(vals)
            avg = total / len(vals)
            first_val = vals[0]
            last_val = vals[-1]
            growth_pct = ((last_val - first_val) / abs(first_val) * 100.0) if first_val != 0 else 0.0

            summaries[col] = {
                "total": round(total, 2),
                "avg": round(avg, 2),
                "min": round(min(vals), 2),
                "max": round(max(vals), 2),
                "start": round(first_val, 2),
                "end": round(last_val, 2),
                "change_pct": round(growth_pct, 1)
            }
        return summaries

    def error(self, message: str, line: int, column: int, suggestion: str = None):
        snippet = extract_snippet(self.source, line, column, 1)
        diag = Diagnostic(
            phase="Runtime",
            message=message,
            line=line,
            column=column,
            length=1,
            severity="error",
            suggestion=suggestion,
            snippet=snippet
        )
        raise CompilerException(diag)
