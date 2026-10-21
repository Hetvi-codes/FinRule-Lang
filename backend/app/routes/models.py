from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from ..models.schemas import ModelCreate, ModelUpdate, ModelResponse, ModelVersionResponse
from ..auth_utils import get_current_user
from ..templates_data import TEMPLATES
from ..db import db

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=List[ModelResponse])
async def list_models(project_id: str = Query(...), current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    models = await db.list_models(project_id, user_id)

    # If project is empty, create initial model from template #1
    if not models:
        initial_tpl = TEMPLATES[0]
        model_doc = {
            "project_id": project_id,
            "name": initial_tpl["name"],
            "source_code": initial_tpl["source_code"],
            "description": initial_tpl["description"],
            "user_id": user_id
        }
        model_id = await db.create_model(model_doc)
        model_doc["_id"] = model_id
        # Also create initial version
        await db.add_version({
            "model_id": model_id,
            "source_code": initial_tpl["source_code"],
            "commit_message": "Initial template version",
            "created_at": model_doc.get("created_at")
        })
        models = [model_doc]

    return [
        ModelResponse(
            id=str(m.get("_id", m.get("id"))),
            project_id=m["project_id"],
            name=m["name"],
            source_code=m.get("source_code", ""),
            description=m.get("description", ""),
            created_at=m.get("created_at"),
            updated_at=m.get("updated_at")
        )
        for m in models
    ]


@router.post("", response_model=ModelResponse)
async def create_model(req: ModelCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    doc = {
        "project_id": req.project_id,
        "name": req.name,
        "source_code": req.source_code,
        "description": req.description or "",
        "user_id": user_id
    }
    model_id = await db.create_model(doc)
    doc["_id"] = model_id

    # Add initial version
    await db.add_version({
        "model_id": model_id,
        "source_code": req.source_code,
        "commit_message": "Initial creation",
        "created_at": doc.get("created_at")
    })

    return ModelResponse(
        id=model_id,
        project_id=doc["project_id"],
        name=doc["name"],
        source_code=doc["source_code"],
        description=doc["description"],
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at")
    )


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    m = await db.get_model(model_id, user_id)
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelResponse(
        id=str(m.get("_id", m.get("id"))),
        project_id=m["project_id"],
        name=m["name"],
        source_code=m.get("source_code", ""),
        description=m.get("description", ""),
        created_at=m.get("created_at"),
        updated_at=m.get("updated_at")
    )


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(model_id: str, req: ModelUpdate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    existing = await db.get_model(model_id, user_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Model not found")

    updates = {}
    if req.name is not None:
        updates["name"] = req.name
    if req.description is not None:
        updates["description"] = req.description
    if req.source_code is not None:
        updates["source_code"] = req.source_code

        # If source code changed or commit message was given, record version
        if req.source_code != existing.get("source_code") or req.commit_message:
            await db.add_version({
                "model_id": model_id,
                "source_code": req.source_code,
                "commit_message": req.commit_message or "Code update",
                "created_at": existing.get("updated_at")
            })

    ok = await db.update_model(model_id, user_id, updates)
    if not ok:
        raise HTTPException(status_code=404, detail="Model update failed")

    m = await db.get_model(model_id, user_id)
    return ModelResponse(
        id=str(m.get("_id", m.get("id"))),
        project_id=m["project_id"],
        name=m["name"],
        source_code=m.get("source_code", ""),
        description=m.get("description", ""),
        created_at=m.get("created_at"),
        updated_at=m.get("updated_at")
    )


@router.delete("/{model_id}")
async def delete_model(model_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    ok = await db.delete_model(model_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted"}


@router.get("/{model_id}/versions", response_model=List[ModelVersionResponse])
async def list_model_versions(model_id: str, current_user: dict = Depends(get_current_user)):
    versions = await db.list_versions(model_id)
    return [
        ModelVersionResponse(
            id=str(v.get("_id", v.get("id"))),
            model_id=v["model_id"],
            source_code=v["source_code"],
            commit_message=v.get("commit_message", "Snapshot"),
            created_at=v.get("created_at", "")
        )
        for v in versions
    ]


@router.post("/{model_id}/restore/{version_id}", response_model=ModelResponse)
async def restore_version(model_id: str, version_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    versions = await db.list_versions(model_id)
    target = None
    for v in versions:
        if str(v.get("_id", v.get("id"))) == version_id:
            target = v
            break

    if not target:
        raise HTTPException(status_code=404, detail="Version not found")

    await db.update_model(model_id, user_id, {"source_code": target["source_code"]})
    await db.add_version({
        "model_id": model_id,
        "source_code": target["source_code"],
        "commit_message": f"Restored from version {version_id[:8]}"
    })

    m = await db.get_model(model_id, user_id)
    return ModelResponse(
        id=str(m.get("_id", m.get("id"))),
        project_id=m["project_id"],
        name=m["name"],
        source_code=m.get("source_code", ""),
        description=m.get("description", ""),
        created_at=m.get("created_at"),
        updated_at=m.get("updated_at")
    )
