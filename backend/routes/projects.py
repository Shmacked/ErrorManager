from fastapi import APIRouter, Depends, HTTPException
from backend.pydantic_models.project_models import ProjectInput, ProjectUpdate, ProjectResponse
from backend.database import get_db
from sqlalchemy.orm import Session
from backend.db_models.db_models import Project
from typing import List

router = APIRouter(
    prefix="/projects",
    tags=["projects"],
)

@router.get("/", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects

@router.post("/", response_model=ProjectResponse)
def create_project(project: ProjectInput, db: Session = Depends(get_db)):
    new_project = Project(**project.model_dump())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project

@router.get("/id/{project_id}", response_model=ProjectResponse)
def get_project_by_id(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.get("/uuid/{project_uuid}", response_model=ProjectResponse)
def get_project_by_uuid(project_uuid: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.project_uuid == project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/id/{project_id}", response_model=ProjectResponse)
def update_project_by_id(project_id: int, project: ProjectUpdate, db: Session = Depends(get_db)):
    project_query = db.query(Project).filter(Project.id == project_id).first()
    if not project_query:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project.model_dump(exclude_unset=True).items():
        setattr(project_query, key, value)
    db.commit()
    db.refresh(project_query)
    return project_query

@router.put("/uuid/{project_uuid}", response_model=ProjectResponse)
def update_project_by_uuid(project_uuid: str, project: ProjectUpdate, db: Session = Depends(get_db)):
    project_query = db.query(Project).filter(Project.project_uuid == project_uuid).first()
    if not project_query:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project.model_dump(exclude_unset=True).items():
        setattr(project_query, key, value)
    db.commit()
    db.refresh(project_query)
    return project_query

@router.patch("/id/{project_id}", response_model=ProjectResponse)
def patch_project_by_id(project_id: int, project: ProjectUpdate, db: Session = Depends(get_db)):
    project_query = db.query(Project).filter(Project.id == project_id).first()
    if not project_query:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project.model_dump(exclude_unset=True).items():
        setattr(project_query, key, value)
    db.commit()
    db.refresh(project_query)
    return project_query

@router.patch("/uuid/{project_uuid}", response_model=ProjectResponse)
def patch_project_by_uuid(project_uuid: str, project: ProjectUpdate, db: Session = Depends(get_db)):
    project_query = db.query(Project).filter(Project.project_uuid == project_uuid).first()
    if not project_query:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in project.model_dump(exclude_unset=True).items():
        setattr(project_query, key, value)
    db.commit()
    db.refresh(project_query)
    return project_query

@router.delete("/id/{project_id}", response_model=ProjectResponse)
def delete_project_by_id(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return project

@router.delete("/uuid/{project_uuid}", response_model=ProjectResponse)
def delete_project_by_uuid(project_uuid: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.project_uuid == project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return project
