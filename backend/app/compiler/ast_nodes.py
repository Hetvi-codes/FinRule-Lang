from dataclasses import dataclass, field
from typing import List, Optional, Any, Union


@dataclass
class ASTNode:
    line: int = 0
    column: int = 0

    def to_dict(self) -> dict:
        raise NotImplementedError


# --- Expressions ---

@dataclass
class ExprNode(ASTNode):
    pass


@dataclass
class NumberLiteralNode(ExprNode):
    value: Union[int, float] = 0

    def to_dict(self) -> dict:
        return {
            "type": "NumberLiteral",
            "value": self.value,
            "line": self.line,
            "column": self.column
        }


@dataclass
class StringLiteralNode(ExprNode):
    value: str = ""

    def to_dict(self) -> dict:
        return {
            "type": "StringLiteral",
            "value": self.value,
            "line": self.line,
            "column": self.column
        }


@dataclass
class IdentifierNode(ExprNode):
    name: str = ""

    def to_dict(self) -> dict:
        return {
            "type": "Identifier",
            "name": self.name,
            "line": self.line,
            "column": self.column
        }


@dataclass
class BinaryOpNode(ExprNode):
    op: str = ""
    left: ExprNode = None
    right: ExprNode = None

    def to_dict(self) -> dict:
        return {
            "type": "BinaryOp",
            "operator": self.op,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None,
            "line": self.line,
            "column": self.column
        }


@dataclass
class UnaryOpNode(ExprNode):
    op: str = ""
    operand: ExprNode = None

    def to_dict(self) -> dict:
        return {
            "type": "UnaryOp",
            "operator": self.op,
            "operand": self.operand.to_dict() if self.operand else None,
            "line": self.line,
            "column": self.column
        }


@dataclass
class FunctionCallNode(ExprNode):
    name: str = ""
    args: List[ExprNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "FunctionCall",
            "name": self.name,
            "arguments": [arg.to_dict() for arg in self.args],
            "line": self.line,
            "column": self.column
        }


# --- Statements ---

@dataclass
class StatementNode(ASTNode):
    pass


@dataclass
class AssignNode(StatementNode):
    target: str = ""
    expr: ExprNode = None

    def to_dict(self) -> dict:
        return {
            "type": "AssignStatement",
            "target": self.target,
            "expression": self.expr.to_dict() if self.expr else None,
            "line": self.line,
            "column": self.column
        }


@dataclass
class ForLoopNode(StatementNode):
    iterator: str = ""
    start_expr: ExprNode = None
    end_expr: ExprNode = None
    body: List[StatementNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "ForLoopStatement",
            "iterator": self.iterator,
            "start": self.start_expr.to_dict() if self.start_expr else None,
            "end": self.end_expr.to_dict() if self.end_expr else None,
            "body": [stmt.to_dict() for stmt in self.body],
            "line": self.line,
            "column": self.column
        }


@dataclass
class IfNode(StatementNode):
    condition: ExprNode = None
    then_body: List[StatementNode] = field(default_factory=list)
    else_body: Optional[List[StatementNode]] = None

    def to_dict(self) -> dict:
        res = {
            "type": "IfStatement",
            "condition": self.condition.to_dict() if self.condition else None,
            "then": [stmt.to_dict() for stmt in self.then_body],
            "line": self.line,
            "column": self.column
        }
        if self.else_body is not None:
            res["else"] = [stmt.to_dict() for stmt in self.else_body]
        return res


@dataclass
class OutputNode(StatementNode):
    variables: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "OutputStatement",
            "variables": self.variables,
            "line": self.line,
            "column": self.column
        }


# --- Top Level Declarations ---

@dataclass
class ModelNode(ASTNode):
    name: str = ""
    body: List[StatementNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "ModelDeclaration",
            "name": self.name,
            "body": [stmt.to_dict() for stmt in self.body],
            "line": self.line,
            "column": self.column
        }


@dataclass
class ScenarioNode(ASTNode):
    name: str = ""
    body: List[StatementNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "ScenarioDeclaration",
            "name": self.name,
            "body": [stmt.to_dict() for stmt in self.body],
            "line": self.line,
            "column": self.column
        }


@dataclass
class ProgramNode(ASTNode):
    models: List[ModelNode] = field(default_factory=list)
    scenarios: List[ScenarioNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": "Program",
            "models": [m.to_dict() for m in self.models],
            "scenarios": [s.to_dict() for s in self.scenarios],
            "line": self.line,
            "column": self.column
        }
