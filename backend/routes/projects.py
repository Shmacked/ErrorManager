from fastapi import APIRouter, Depends, HTTPException
from pydantic_models.error_models import ProjectRequest, ProjectUpdate
from database import get_db
from sqlalchemy.orm import Session
from db_models.error_models import Project

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

@router.get("/")
def get_projects():
    db = next(get_db())
    projects = db.query(Project).all()
    return projects

@router.post("/")
def create_project(project: ProjectRequest):
    return {"message": "Project created"}

@router.get("/{project_id}")
def get_project(project_id: int):
    return {"message": "Project retrieved"}

@router.put("/{project_id}")
def update_project(project_id: int, project: ProjectUpdate):
    return {"message": "Project updated"}

@router.patch("/{project_id}")
def patch_project(project_id: int, project: ProjectUpdate):
    return {"message": "Project patched"}

@router.delete("/{project_id}")
def delete_project(project_id: int):
    return {"message": "Project deleted"}
