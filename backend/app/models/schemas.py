from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ModelCreate(BaseModel):
    project_id: str
    name: str
    source_code: str = ""
    description: Optional[str] = ""


class ModelUpdate(BaseModel):
    name: Optional[str] = None
    source_code: Optional[str] = None
    description: Optional[str] = None
    commit_message: Optional[str] = None


class ModelVersionResponse(BaseModel):
    id: str
    model_id: str
    source_code: str
    commit_message: str
    created_at: str


class ModelResponse(BaseModel):
    id: str
    project_id: str
    name: str
    source_code: str
    description: Optional[str] = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CompileRequest(BaseModel):
    source_code: str
    model_id: Optional[str] = None
    scenario_name: Optional[str] = None


class CompileResponse(BaseModel):
    success: bool
    timings: Dict[str, float]
    model_name: Optional[str] = None
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    summaries: Dict[str, Any] = {}
    scenarios: Dict[str, Any] = {}
    compiler_studio: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class TemplateResponse(BaseModel):
    id: str
    name: str
    category: str
    description: str
    source_code: str


class CustomTemplateCreate(BaseModel):
    name: str
    category: Optional[str] = "Custom"
    description: Optional[str] = ""
    source_code: str

