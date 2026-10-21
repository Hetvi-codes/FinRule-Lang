import time
from typing import Dict, Any, Optional
from .tokens import Token
from .lexer import Lexer
from .parser import Parser
from .semantic import SemanticAnalyzer
from .ir import IRGenerator
from .interpreter import Interpreter
from .diagnostics import CompilerException, Diagnostic


def compile_and_execute(source_code: str, scenario_name: Optional[str] = None) -> Dict[str, Any]:
    start_total = time.perf_counter()
    timings = {}

    try:
        # Phase 1: Lexical Analysis
        t0 = time.perf_counter()
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
        timings["lexer_ms"] = round((time.perf_counter() - t0) * 1000, 3)

        # Phase 2: Syntax Analysis (Parser -> AST)
        t0 = time.perf_counter()
        parser = Parser(tokens, source=source_code)
        ast = parser.parse()
        timings["parser_ms"] = round((time.perf_counter() - t0) * 1000, 3)

        # Phase 3: Semantic Analysis (Symbol Table + Type Checking)
        t0 = time.perf_counter()
        analyzer = SemanticAnalyzer(source=source_code)
        symbol_history = analyzer.analyze(ast)
        timings["semantic_ms"] = round((time.perf_counter() - t0) * 1000, 3)

        # Phase 4: Intermediate Representation (IR Generation)
        t0 = time.perf_counter()
        ir_gen = IRGenerator()
        ir_instructions = ir_gen.generate(ast)
        timings["ir_ms"] = round((time.perf_counter() - t0) * 1000, 3)

        # Phase 5: Interpretation / Execution
        t0 = time.perf_counter()
        interpreter = Interpreter(source=source_code)
        exec_result = interpreter.execute_program(ast, selected_scenario_name=scenario_name)
        timings["execution_ms"] = round((time.perf_counter() - t0) * 1000, 3)

        timings["total_ms"] = round((time.perf_counter() - start_total) * 1000, 3)

        return {
            "success": True,
            "timings": timings,
            "model_name": exec_result.get("model_name", "Untitled Model"),
            "columns": exec_result.get("columns", []),
            "rows": exec_result.get("rows", []),
            "summaries": exec_result.get("summaries", {}),
            "scenarios": exec_result.get("scenarios", {}),
            # Academic Compiler Artifacts for UI inspection
            "compiler_studio": {
                "tokens": [t.to_dict() for t in tokens if t.type.name != "EOF"],
                "ast": ast.to_dict(),
                "symbol_table": [s.to_dict() for s in symbol_history],
                "ir": [instr.to_dict() for instr in ir_instructions],
                "diagnostics": [d.to_dict() for d in analyzer.diagnostics if d.severity == "warning"]
            },
            "error": None
        }

    except CompilerException as ce:
        timings["total_ms"] = round((time.perf_counter() - start_total) * 1000, 3)
        return {
            "success": False,
            "timings": timings,
            "error": ce.diagnostic.to_dict(),
            "columns": [],
            "rows": [],
            "summaries": {},
            "scenarios": {},
            "compiler_studio": None
        }
    except Exception as e:
        timings["total_ms"] = round((time.perf_counter() - start_total) * 1000, 3)
        diag = Diagnostic(
            phase="Compiler",
            message=str(e),
            line=1,
            column=1,
            severity="error"
        )
        return {
            "success": False,
            "timings": timings,
            "error": diag.to_dict(),
            "columns": [],
            "rows": [],
            "summaries": {},
            "scenarios": {},
            "compiler_studio": None
        }
