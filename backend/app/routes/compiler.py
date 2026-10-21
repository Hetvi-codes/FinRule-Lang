from fastapi import APIRouter, Depends
from ..models.schemas import CompileRequest, CompileResponse
from ..compiler.pipeline import compile_and_execute
from ..auth_utils import get_current_user
from ..db import db

router = APIRouter(prefix="", tags=["Compiler"])


@router.post("/execute", response_model=CompileResponse)
async def execute_model_script(req: CompileRequest, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))

    result = compile_and_execute(req.source_code, scenario_name=req.scenario_name)

    # Log execution
    exec_doc = {
        "user_id": user_id,
        "model_id": req.model_id or "adhoc",
        "scenario_name": req.scenario_name or "Base Model",
        "success": result["success"],
        "timings": result["timings"],
        "row_count": len(result.get("rows", [])),
        "columns": result.get("columns", []),
        "error": result.get("error")
    }
    await db.log_execution(exec_doc)

    return CompileResponse(
        success=result["success"],
        timings=result["timings"],
        model_name=result.get("model_name"),
        columns=result.get("columns", []),
        rows=result.get("rows", []),
        summaries=result.get("summaries", {}),
        scenarios=result.get("scenarios", {}),
        compiler_studio=result.get("compiler_studio"),
        error=result.get("error")
    )
