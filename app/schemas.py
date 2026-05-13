from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from app.models import TaskStatus, TaskPriority


# ---------------------------------------------------------------------------
# Shared config
# ---------------------------------------------------------------------------

class _OrmBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# USER SCHEMAS
# ===========================================================================

class UserCreate(BaseModel):
    email: EmailStr
    username: str = Field(
        ..., min_length=3, max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Alphanumeric, underscores, and hyphens only.",
    )
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=200)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None


class UserResponse(_OrmBase):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


# ===========================================================================
# AUTH SCHEMAS
# ===========================================================================

class LoginRequest(BaseModel):
    username: str = Field(..., description="username or email")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None


# ===========================================================================
# TASK SCHEMAS
# ===========================================================================

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None


class TaskUpdate(BaseModel):
    """Full update – all fields required (PUT)."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime] = None
    is_completed: bool


class TaskPatch(BaseModel):
    """Partial update – all fields optional (PATCH)."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None


class TaskResponse(_OrmBase):
    id: uuid.UUID
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[datetime]
    is_completed: bool
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    tasks: list[TaskResponse]
