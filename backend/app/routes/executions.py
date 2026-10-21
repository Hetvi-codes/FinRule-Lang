from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Any
from ..auth_utils import get_current_user
from ..db import db

router = APIRouter(prefix="/executions", tags=["Executions"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_user_executions(
    limit: int = Query(30, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    user_id = str(current_user.get("_id", current_user.get("id")))
    executions = await db.list_executions(user_id, limit=limit)
    return [
        {
            "id": str(e.get("_id", e.get("id"))),
            "model_id": e.get("model_id"),
            "scenario_name": e.get("scenario_name", "Base Model"),
            "success": e.get("success", False),
            "timings": e.get("timings", {}),
            "row_count": e.get("row_count", 0),
            "columns": e.get("columns", []),
            "created_at": e.get("created_at"),
            "error": e.get("error")
        }
        for e in executions
    ]
