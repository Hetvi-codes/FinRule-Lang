from typing import List, Any, Optional
from dataclasses import dataclass
from .ast_nodes import (
    ProgramNode, ModelNode, ScenarioNode, StatementNode,
    AssignNode, ForLoopNode, IfNode, OutputNode,
    ExprNode, NumberLiteralNode, StringLiteralNode, IdentifierNode,
    BinaryOpNode, UnaryOpNode, FunctionCallNode
)


@dataclass
class IRInstruction:
    op: str                 # e.g., "LOAD_CONST", "ASSIGN", "ADD", "CALL", "JUMP_IF_FALSE", "JUMP", "LABEL", "OUTPUT"
    arg1: Optional[Any] = None
    arg2: Optional[Any] = None
    result: Optional[str] = None
    line: int = 0

    def to_dict(self) -> dict:
        return {
            "op": self.op,
            "arg1": str(self.arg1) if self.arg1 is not None else None,
            "arg2": str(self.arg2) if self.arg2 is not None else None,
            "result": str(self.result) if self.result is not None else None,
            "line": self.line
        }

    def __repr__(self) -> str:
        parts = [f"{self.op:<14}"]
        if self.result:
            parts.append(f"{self.result} = ")
        if self.arg1 is not None:
            parts.append(str(self.arg1))
        if self.arg2 is not None:
            parts.append(f", {self.arg2}")
        return "".join(parts)


class IRGenerator:
    def __init__(self):
        self.instructions: List[IRInstruction] = []
        self.temp_counter = 0
        self.label_counter = 0

    def new_temp(self) -> str:
        self.temp_counter += 1
        return f"t{self.temp_counter}"

    def new_label(self, prefix: str = "L") -> str:
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def emit(self, op: str, arg1: Any = None, arg2: Any = None, result: str = None, line: int = 0) -> IRInstruction:
        instr = IRInstruction(op=op, arg1=arg1, arg2=arg2, result=result, line=line)
        self.instructions.append(instr)
        return instr

    def generate(self, program: ProgramNode) -> List[IRInstruction]:
        self.instructions = []
        self.temp_counter = 0
        self.label_counter = 0

        for model in program.models:
            self.emit("MODEL_BEGIN", arg1=model.name, line=model.line)
            for stmt in model.body:
                self.gen_statement(stmt)
            self.emit("MODEL_END", arg1=model.name, line=model.line)

        for scenario in program.scenarios:
            self.emit("SCENARIO_BEGIN", arg1=scenario.name, line=scenario.line)
            for stmt in scenario.body:
                self.gen_statement(stmt)
            self.emit("SCENARIO_END", arg1=scenario.name, line=scenario.line)

        return self.instructions

    def gen_statement(self, stmt: StatementNode):
        if isinstance(stmt, AssignNode):
            res_temp = self.gen_expression(stmt.expr)
            self.emit("STORE_VAR", arg1=res_temp, result=stmt.target, line=stmt.line)

        elif isinstance(stmt, ForLoopNode):
            start_temp = self.gen_expression(stmt.start_expr)
            end_temp = self.gen_expression(stmt.end_expr)

            # Store loop counter initial value
            self.emit("STORE_VAR", arg1=start_temp, result=stmt.iterator, line=stmt.line)

            loop_start_lbl = self.new_label("LOOP_START")
            loop_end_lbl = self.new_label("LOOP_END")

            self.emit("LABEL", arg1=loop_start_lbl, line=stmt.line)
            
            # Check condition: iterator <= end
            cond_temp = self.new_temp()
            self.emit("LTE", arg1=stmt.iterator, arg2=end_temp, result=cond_temp, line=stmt.line)
            self.emit("JUMP_IF_FALSE", arg1=cond_temp, arg2=loop_end_lbl, line=stmt.line)

            # Body
            for inner_stmt in stmt.body:
                self.gen_statement(inner_stmt)

            # Increment iterator
            incr_temp = self.new_temp()
            self.emit("ADD", arg1=stmt.iterator, arg2=1, result=incr_temp, line=stmt.line)
            self.emit("STORE_VAR", arg1=incr_temp, result=stmt.iterator, line=stmt.line)

            # Jump back
            self.emit("JUMP", arg1=loop_start_lbl, line=stmt.line)
            self.emit("LABEL", arg1=loop_end_lbl, line=stmt.line)

        elif isinstance(stmt, IfNode):
            cond_temp = self.gen_expression(stmt.condition)
            else_lbl = self.new_label("ELSE") if stmt.else_body else None
            end_lbl = self.new_label("ENDIF")

            target_lbl = else_lbl if else_lbl else end_lbl
            self.emit("JUMP_IF_FALSE", arg1=cond_temp, arg2=target_lbl, line=stmt.line)

            # Then body
            for inner_stmt in stmt.then_body:
                self.gen_statement(inner_stmt)

            if stmt.else_body:
                self.emit("JUMP", arg1=end_lbl, line=stmt.line)
                self.emit("LABEL", arg1=else_lbl, line=stmt.line)
                for inner_stmt in stmt.else_body:
                    self.gen_statement(inner_stmt)

            self.emit("LABEL", arg1=end_lbl, line=stmt.line)

        elif isinstance(stmt, OutputNode):
            self.emit("EMIT_RECORD", arg1=",".join(stmt.variables), line=stmt.line)

    def gen_expression(self, expr: ExprNode) -> str:
        if isinstance(expr, NumberLiteralNode):
            t = self.new_temp()
            self.emit("LOAD_CONST", arg1=expr.value, result=t, line=expr.line)
            return t

        if isinstance(expr, StringLiteralNode):
            t = self.new_temp()
            self.emit("LOAD_CONST", arg1=f'"{expr.value}"', result=t, line=expr.line)
            return t

        if isinstance(expr, IdentifierNode):
            t = self.new_temp()
            self.emit("LOAD_VAR", arg1=expr.name, result=t, line=expr.line)
            return t

        if isinstance(expr, BinaryOpNode):
            t1 = self.gen_expression(expr.left)
            t2 = self.gen_expression(expr.right)
            t_res = self.new_temp()
            op_map = {
                "+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV", "%": "MOD", "^": "POW",
                "==": "EQ", "!=": "NEQ", "<": "LT", "<=": "LTE", ">": "GT", ">=": "GTE",
                "and": "AND", "or": "OR"
            }
            ir_op = op_map.get(expr.op, expr.op.upper())
            self.emit(ir_op, arg1=t1, arg2=t2, result=t_res, line=expr.line)
            return t_res

        if isinstance(expr, UnaryOpNode):
            t1 = self.gen_expression(expr.operand)
            t_res = self.new_temp()
            ir_op = "NEG" if expr.op == "-" else ("NOT" if expr.op == "not" else "NOP")
            self.emit(ir_op, arg1=t1, result=t_res, line=expr.line)
            return t_res

        if isinstance(expr, FunctionCallNode):
            arg_temps = [self.gen_expression(arg) for arg in expr.args]
            t_res = self.new_temp()
            self.emit("CALL_FINANCIAL", arg1=expr.name.upper(), arg2=",".join(arg_temps), result=t_res, line=expr.line)
            return t_res

        return ""
