from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from ..models.schemas import TemplateResponse, ModelResponse, CustomTemplateCreate
from ..templates_data import TEMPLATES
from ..auth_utils import get_current_user
from ..db import db

router = APIRouter(prefix="/templates", tags=["Templates"])


@router.get("", response_model=List[TemplateResponse])
async def list_templates():
    return [TemplateResponse(**t) for t in TEMPLATES]


@router.get("/custom", response_model=List[TemplateResponse])
async def list_custom_templates(current_user: Optional[dict] = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id"))) if current_user else None
    items = await db.list_custom_templates(user_id)
    return [
        TemplateResponse(
            id=str(item.get("_id", item.get("id"))),
            name=item.get("name", "Custom Model"),
            category=item.get("category", "Custom"),
            description=item.get("description", ""),
            source_code=item.get("source_code", "")
        )
        for item in items
    ]


@router.post("/custom", response_model=TemplateResponse)
async def create_custom_template(req: CustomTemplateCreate, current_user: Optional[dict] = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id"))) if current_user else None
    doc = {
        "name": req.name,
        "category": req.category or "Custom",
        "description": req.description or "",
        "source_code": req.source_code,
        "user_id": user_id
    }
    template_id = await db.create_custom_template(doc)
    return TemplateResponse(
        id=template_id,
        name=doc["name"],
        category=doc["category"],
        description=doc["description"],
        source_code=doc["source_code"]
    )


@router.delete("/custom/{template_id}")
async def delete_custom_template(template_id: str, current_user: Optional[dict] = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id"))) if current_user else None
    deleted = await db.delete_custom_template(template_id, user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Custom template not found")
    return {"message": "Custom template deleted successfully"}


@router.post("/{template_id}/clone", response_model=ModelResponse)
async def clone_template(template_id: str, project_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))

    # Check built-in templates first
    tpl = next((t for t in TEMPLATES if t["id"] == template_id), None)
    if not tpl:
        # Check custom templates
        custom_items = await db.list_custom_templates(user_id)
        tpl = next((t for t in custom_items if str(t.get("_id", t.get("id"))) == template_id), None)

    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")

    model_doc = {
        "project_id": project_id,
        "name": tpl["name"],
        "source_code": tpl["source_code"],
        "description": tpl.get("description", ""),
        "user_id": user_id
    }
    model_id = await db.create_model(model_doc)
    model_doc["_id"] = model_id

    await db.add_version({
        "model_id": model_id,
        "source_code": tpl["source_code"],
        "commit_message": f"Cloned from template: {tpl['name']}"
    })

    return ModelResponse(
        id=model_id,
        project_id=project_id,
        name=model_doc["name"],
        source_code=model_doc["source_code"],
        description=model_doc["description"],
        created_at=model_doc.get("created_at"),
        updated_at=model_doc.get("updated_at")
    )

