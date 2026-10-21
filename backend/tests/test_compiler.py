import os
import sys
import pytest

# Ensure both workspace root and backend directory are in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from backend.app.compiler.lexer import Lexer
    from backend.app.compiler.parser import Parser
    from backend.app.compiler.semantic import SemanticAnalyzer
    from backend.app.compiler.ir import IRGenerator
    from backend.app.compiler.interpreter import Interpreter
    from backend.app.compiler.pipeline import compile_and_execute
    from backend.app.compiler.tokens import TokenType
    from backend.app.compiler.diagnostics import CompilerException
except ModuleNotFoundError:
    from app.compiler.lexer import Lexer
    from app.compiler.parser import Parser
    from app.compiler.semantic import SemanticAnalyzer
    from app.compiler.ir import IRGenerator
    from app.compiler.interpreter import Interpreter
    from app.compiler.pipeline import compile_and_execute
    from app.compiler.tokens import TokenType
    from app.compiler.diagnostics import CompilerException


def test_lexer_tokenization():
    code = """
    // Model definition
    model "SaaS Test" {
        starting_mrr = 50000
        rate = 0.05
    }
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.MODEL, TokenType.STRING, TokenType.LBRACE,
        TokenType.IDENTIFIER, TokenType.ASSIGN, TokenType.NUMBER,
        TokenType.IDENTIFIER, TokenType.ASSIGN, TokenType.NUMBER,
        TokenType.RBRACE
    ]


def test_parser_and_ast():
    code = """
    model "Test" {
        for month in 1 to 12 {
            revenue = 1000 * month
            output month, revenue
        }
    }
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source=code)
    ast = parser.parse()
    assert len(ast.models) == 1
    assert ast.models[0].name == "Test"
    assert len(ast.models[0].body) == 1  # ForLoopNode


def test_semantic_undefined_var():
    code = """
    model "Bad" {
        x = unknown_var + 10
    }
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source=code)
    ast = parser.parse()
    analyzer = SemanticAnalyzer(source=code)
    with pytest.raises(CompilerException) as exc:
        analyzer.analyze(ast)
    assert "Undefined variable 'unknown_var'" in str(exc.value)


def test_semantic_division_by_zero():
    code = """
    model "DivZero" {
        x = 100 / 0
    }
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source=code)
    ast = parser.parse()
    analyzer = SemanticAnalyzer(source=code)
    with pytest.raises(CompilerException) as exc:
        analyzer.analyze(ast)
    assert "Division by constant zero detected" in str(exc.value)


def test_ir_generation():
    code = """
    model "IR Test" {
        x = 10 + 20 * 3
    }
    """
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens, source=code)
    ast = parser.parse()
    ir_gen = IRGenerator()
    instructions = ir_gen.generate(ast)
    ops = [i.op for i in instructions]
    assert "MUL" in ops
    assert "ADD" in ops
    assert "STORE_VAR" in ops


def test_full_pipeline_srs_example():
    code = """
    model "SaaS Growth Model" {
      starting_mrr = 75000
      monthly_growth = 0.055
      churn = 0.02
      cogs_rate = 0.22
      opex = 38000

      for month in 1 to 24 {
        mrr = starting_mrr * (1 + monthly_growth - churn) ^ month
        revenue = mrr
        gross_profit = revenue * (1 - cogs_rate)
        net_profit = gross_profit - opex

        output month, mrr, revenue, gross_profit, net_profit
      }
    }

    scenario "Aggressive Growth" {
      monthly_growth = 0.09
      churn = 0.015
    }
    """
    result = compile_and_execute(code)
    assert result["success"] is True
    assert len(result["rows"]) == 24
    assert "month" in result["columns"]
    assert "mrr" in result["columns"]
    assert "revenue" in result["columns"]
    assert "net_profit" in result["columns"]

    # Check that the scenario was evaluated
    assert "Aggressive Growth" in result["scenarios"]
    scen_rows = result["scenarios"]["Aggressive Growth"]["rows"]
    assert len(scen_rows) == 24
    # Aggressive growth revenue in month 24 should be higher than base model
    assert scen_rows[23]["revenue"] > result["rows"][23]["revenue"]

    # Check compiler studio artifacts
    studio = result["compiler_studio"]
    assert len(studio["tokens"]) > 10
    assert studio["ast"] is not None
    assert len(studio["symbol_table"]) > 5
    assert len(studio["ir"]) > 10
