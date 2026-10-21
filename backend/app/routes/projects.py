from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from ..auth_utils import get_current_user
from ..db import db

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("", response_model=List[ProjectResponse])
async def list_user_projects(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    projects = await db.list_projects(user_id)
    # If user has no projects, create a default "Strategic Finance" project with SaaS Growth Model
    if not projects:
        default_proj = {
            "name": "Strategic Finance 2026",
            "description": "Primary workspace for corporate financial models and forecasting.",
            "user_id": user_id
        }
        proj_id = await db.create_project(default_proj)
        default_proj["_id"] = proj_id
        projects = [default_proj]

    return [
        ProjectResponse(
            id=str(p.get("_id", p.get("id"))),
            name=p["name"],
            description=p.get("description", ""),
            user_id=p["user_id"],
            created_at=p.get("created_at"),
            updated_at=p.get("updated_at")
        )
        for p in projects
    ]


@router.post("", response_model=ProjectResponse)
async def create_project(req: ProjectCreate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    doc = {
        "name": req.name,
        "description": req.description or "",
        "user_id": user_id
    }
    proj_id = await db.create_project(doc)
    doc["_id"] = proj_id
    return ProjectResponse(
        id=proj_id,
        name=doc["name"],
        description=doc["description"],
        user_id=user_id,
        created_at=doc.get("created_at"),
        updated_at=doc.get("updated_at")
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    proj = await db.get_project(project_id, user_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(
        id=str(proj.get("_id", proj.get("id"))),
        name=proj["name"],
        description=proj.get("description", ""),
        user_id=proj["user_id"],
        created_at=proj.get("created_at"),
        updated_at=proj.get("updated_at")
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, req: ProjectUpdate, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    updates = {}
    if req.name is not None:
        updates["name"] = req.name
    if req.description is not None:
        updates["description"] = req.description

    ok = await db.update_project(project_id, user_id, updates)
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    proj = await db.get_project(project_id, user_id)
    return ProjectResponse(
        id=str(proj.get("_id", proj.get("id"))),
        name=proj["name"],
        description=proj.get("description", ""),
        user_id=proj["user_id"],
        created_at=proj.get("created_at"),
        updated_at=proj.get("updated_at")
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("_id", current_user.get("id")))
    ok = await db.delete_project(project_id, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project and associated models deleted"}
