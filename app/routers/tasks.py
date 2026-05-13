"""
routers/tasks.py – Full CRUD (POST, GET, PUT, PATCH, DELETE) for Tasks.
All routes require authentication via FastAPI Depends.
"""
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Task, TaskPriority, TaskStatus, User
from app.schemas import (
    TaskCreate,
    TaskListResponse,
    TaskPatch,
    TaskResponse,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: ownership guard
# ---------------------------------------------------------------------------

def _get_task_or_404(task_id: uuid.UUID, owner_id: uuid.UUID, db: Session) -> Task:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.owner_id == owner_id)
        .first()
    )
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found.")
    return task


# ---------------------------------------------------------------------------
# POST /tasks – Create a task
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = Task(**payload.model_dump(), owner_id=current_user.id)
    try:
        db.add(task)
        db.commit()
        db.refresh(task)
        logger.info("Task created: id=%s owner=%s", task.id, current_user.id)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to create task: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while creating task: {str(exc)}",
        )
    return task


# ---------------------------------------------------------------------------
# GET /tasks – List all tasks (paginated + filterable)
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=TaskListResponse,
    summary="List tasks with pagination and optional filters",
)
def list_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    # FIX: renamed from 'status' → 'task_status' to avoid collision with
    # the imported fastapi.status module (was causing a silent 500 error)
    task_status: Optional[TaskStatus] = Query(None, alias="status"),
    priority: Optional[TaskPriority] = Query(None),
    is_completed: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search in title"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Task).filter(Task.owner_id == current_user.id)

    # Filters
    if task_status is not None:
        query = query.filter(Task.status == task_status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    total = query.count()
    tasks = (
        query
        .order_by(Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return TaskListResponse(total=total, page=page, page_size=page_size, tasks=tasks)


# ---------------------------------------------------------------------------
# GET /tasks/{task_id} – Retrieve a single task
# ---------------------------------------------------------------------------

@router.get("/{task_id}", response_model=TaskResponse, summary="Get a task by ID")
def get_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_task_or_404(task_id, current_user.id, db)


# ---------------------------------------------------------------------------
# PUT /tasks/{task_id} – Full update
# ---------------------------------------------------------------------------

@router.put("/{task_id}", response_model=TaskResponse, summary="Fully update a task (PUT)")
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, current_user.id, db)
    for field, value in payload.model_dump().items():
        setattr(task, field, value)
    try:
        db.commit()
        db.refresh(task)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to update task %s: %s", task_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while updating task: {str(exc)}",
        )
    return task


# ---------------------------------------------------------------------------
# PATCH /tasks/{task_id} – Partial update
# ---------------------------------------------------------------------------

@router.patch("/{task_id}", response_model=TaskResponse, summary="Partially update a task (PATCH)")
def patch_task(
    task_id: uuid.UUID,
    payload: TaskPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, current_user.id, db)
    # Only update fields explicitly set by the caller
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    try:
        db.commit()
        db.refresh(task)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to patch task %s: %s", task_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while patching task: {str(exc)}",
        )
    return task


# ---------------------------------------------------------------------------
# DELETE /tasks/{task_id} – Delete a task
# ---------------------------------------------------------------------------

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, current_user.id, db)
    try:
        db.delete(task)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Failed to delete task %s: %s", task_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while deleting task: {str(exc)}",
        )



# ---------------------------------------------------------------------------
# Helper: ownership guard
# ---------------------------------------------------------------------------

def _get_task_or_404(task_id: uuid.UUID, owner_id: uuid.UUID, db: Session) -> Task:
    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.owner_id == owner_id)
        .first()
    )
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found.")
    return task


# ---------------------------------------------------------------------------
# POST /tasks – Create a task
# ---------------------------------------------------------------------------

@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = Task(**payload.model_dump(), owner_id=current_user.id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# ---------------------------------------------------------------------------
# GET /tasks – List all tasks (paginated + filterable)
# ---------------------------------------------------------------------------

@router.get(
    "/",
    response_model=TaskListResponse,
    summary="List tasks with pagination and optional filters",
)
def list_tasks(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    is_completed: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search in title"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Task).filter(Task.owner_id == current_user.id)

    # Filters
    if status is not None:
        query = query.filter(Task.status == status)
    if priority is not None:
        query = query.filter(Task.priority == priority)
    if is_completed is not None:
        query = query.filter(Task.is_completed == is_completed)
    if search:
        query = query.filter(Task.title.ilike(f"%{search}%"))

    total = query.count()
    tasks = (
        query
        .order_by(Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return TaskListResponse(total=total, page=page, page_size=page_size, tasks=tasks)


# ---------------------------------------------------------------------------
# GET /tasks/{task_id} – Retrieve a single task
# ---------------------------------------------------------------------------

@router.get("/{task_id}", response_model=TaskResponse, summary="Get a task by ID")
def get_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_task_or_404(task_id, current_user.id, db)


# ---------------------------------------------------------------------------
# PUT /tasks/{task_id} – Full update
# ---------------------------------------------------------------------------

@router.put("/{task_id}", response_model=TaskResponse, summary="Fully update a task (PUT)")
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, current_user.id, db)
    for field, value in payload.model_dump().items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


# ---------------------------------------------------------------------------
# PATCH /tasks/{task_id} – Partial update
# ---------------------------------------------------------------------------

@router.patch("/{task_id}", response_model=TaskResponse, summary="Partially update a task (PATCH)")
def patch_task(
    task_id: uuid.UUID,
    payload: TaskPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, current_user.id, db)
    # Only update fields explicitly set by the caller
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


# ---------------------------------------------------------------------------
# DELETE /tasks/{task_id} – Delete a task
# ---------------------------------------------------------------------------

@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = _get_task_or_404(task_id, current_user.id, db)
    db.delete(task)
    db.commit()
