from fastapi import APIRouter, Depends, HTTPException
from backend.pydantic_models.error_models import ErrorLogInput, ErrorLogResponse, ErrorLogUpdate, ErrorLogBase
from backend.database import get_db
from sqlalchemy.orm import Session
from backend.db_models.db_models import ErrorLog, Project
from backend.services.langgraph import get_evaulation_error_log_graph
from typing import List


evaluation_error_log_graph = get_evaulation_error_log_graph()

router = APIRouter(
    prefix="/error-logs",
    tags=["error-logs"],
)

# get the error logs for a project
@router.get("/project_id/{project_id}", response_model=List[ErrorLogResponse])
def get_error_logs_by_project_id(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    error_logs = db.query(ErrorLog).filter(ErrorLog.project_id == project_id).all()
    return error_logs

@router.get("/project_uuid/{project_uuid}", response_model=List[ErrorLogResponse])
def get_error_logs_by_project_uuid(project_uuid: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.project_uuid == project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    error_logs = db.query(ErrorLog).filter(ErrorLog.project_id == project.id).all()
    return error_logs

# create a new error log for a project
@router.post("/project_id/{project_id}", response_model=ErrorLogResponse)
def create_error_log_by_project_id(project_id: int, error_log: ErrorLogInput, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    error_log_response = evaluation_error_log_graph.invoke({"input": error_log.traceback})
    new_error_log = ErrorLogBase.model_validate(error_log_response.get("output"))
    new_error_log = ErrorLog(project_id=project.id, **new_error_log.model_dump())
    db.add(new_error_log)
    db.commit()
    db.refresh(new_error_log)
    return new_error_log

@router.post("/project_uuid/{project_uuid}", response_model=ErrorLogResponse)
def create_error_log_by_project_uuid(project_uuid: str, error_log: ErrorLogInput, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.project_uuid == project_uuid).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    error_log_response = evaluation_error_log_graph.invoke({"input": error_log.traceback})
    new_error_log = ErrorLogBase.model_validate(error_log_response.get("output"))
    new_error_log = ErrorLog(project_id=project.id, **new_error_log.model_dump())
    db.add(new_error_log)
    db.commit()
    db.refresh(new_error_log)
    return new_error_log

@router.get("/id/{error_log_id}", response_model=ErrorLogResponse)
def get_error_log_by_error_log_id(error_log_id: int, db: Session = Depends(get_db)):
    error_log = db.query(ErrorLog).filter(ErrorLog.id == error_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    return error_log

@router.get("/log_id/{error_log_log_id}", response_model=ErrorLogResponse)
def get_error_log_by_error_log_log_id(error_log_log_id: str, db: Session = Depends(get_db)):
    error_log = db.query(ErrorLog).filter(ErrorLog.log_id == error_log_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    return error_log

@router.put("/id/{error_log_id}", response_model=ErrorLogResponse)
def update_error_log_by_error_log_id(error_log_id: int, error_log_update: ErrorLogUpdate, db: Session = Depends(get_db)):
    error_log = db.query(ErrorLog).filter(ErrorLog.id == error_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    
    if "project_id" in error_log_update.model_dump(exclude_unset=True):
        project = db.query(Project).filter(Project.id == error_log_update.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    for key, value in error_log_update.model_dump(exclude_unset=True).items():
        setattr(error_log, key, value)
    db.commit()
    db.refresh(error_log)
    return error_log

@router.put("/log_id/{error_log_log_id}", response_model=ErrorLogResponse)
def update_error_log_by_error_log_log_id(error_log_log_id: str, error_log_update: ErrorLogUpdate, db: Session = Depends(get_db)):
    error_log = db.query(ErrorLog).filter(ErrorLog.log_id == error_log_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    
    if "project_id" in error_log_update.model_dump(exclude_unset=True):
        project = db.query(Project).filter(Project.id == error_log_update.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    for key, value in error_log_update.model_dump(exclude_unset=True).items():
        setattr(error_log, key, value)
    db.commit()
    db.refresh(error_log)
    return error_log

@router.patch("/id/{error_log_id}", response_model=ErrorLogResponse)
def patch_error_log_by_error_log_id(error_log_id: int, error_log_update: ErrorLogUpdate, db: Session = Depends(get_db)):
    error_log = db.query(ErrorLog).filter(ErrorLog.id == error_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    
    if "project_id" in error_log_update.model_dump(exclude_unset=True):
        project = db.query(Project).filter(Project.id == error_log_update.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    for key, value in error_log_update.model_dump(exclude_unset=True).items():
        setattr(error_log, key, value)
    db.commit()
    db.refresh(error_log)
    return error_log

@router.patch("/log_id/{error_log_log_id}", response_model=ErrorLogResponse)
def patch_error_log_by_error_log_log_id(error_log_log_id: str, error_log_update: ErrorLogUpdate, db: Session = Depends(get_db)):
    error_log = db.query(ErrorLog).filter(ErrorLog.log_id == error_log_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    
    if "project_id" in error_log_update.model_dump(exclude_unset=True):
        project = db.query(Project).filter(Project.id == error_log_update.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    for key, value in error_log_update.model_dump(exclude_unset=True).items():
        setattr(error_log, key, value)
    db.commit()
    db.refresh(error_log)
    return error_log

@router.delete("/id/{error_log_id}", response_model=ErrorLogResponse)
def delete_error_log_by_error_log_id(error_log_id: int, db: Session = Depends(get_db)):
    error_log = db.query(ErrorLog).filter(ErrorLog.id == error_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    db.delete(error_log)
    db.commit()
    return error_log

@router.delete("/log_id/{error_log_log_id}", response_model=ErrorLogResponse)
def delete_error_log_by_error_log_log_id(error_log_log_id: str, db: Session = Depends(get_db)):
    error_log = db.query(ErrorLog).filter(ErrorLog.log_id == error_log_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    db.delete(error_log)
    db.commit()
    return error_log

@router.get("/project_id/{error_log_project_id}/id/{error_log_id}", response_model=ErrorLogResponse)
def get_error_log_by_project_id_and_id(error_log_project_id: int, error_log_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == error_log_project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    error_log = db.query(ErrorLog).filter(ErrorLog.project_id == project.id, ErrorLog.id == error_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    return error_log

@router.put("/project_id/{error_log_project_id}/id/{error_log_id}", response_model=ErrorLogResponse)
def update_error_log_by_project_id_and_id(error_log_project_id: int, error_log_id: int, error_log_update: ErrorLogUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == error_log_project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    error_log = db.query(ErrorLog).filter(ErrorLog.project_id == project.id, ErrorLog.id == error_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    for key, value in error_log_update.model_dump(exclude_unset=True).items():
        setattr(error_log, key, value)
    db.commit()
    db.refresh(error_log)
    return error_log

@router.patch("/project_id/{error_log_project_id}/id/{error_log_id}", response_model=ErrorLogResponse)
def patch_error_log_by_project_id_and_id(error_log_project_id: int, error_log_id: int, error_log_update: ErrorLogUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == error_log_project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    error_log = db.query(ErrorLog).filter(ErrorLog.project_id == project.id, ErrorLog.id == error_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    for key, value in error_log_update.model_dump(exclude_unset=True).items():
        setattr(error_log, key, value)
    db.commit()
    db.refresh(error_log)
    return error_log

@router.delete("/project_id/{error_log_project_id}/id/{error_log_id}", response_model=ErrorLogResponse)
def delete_error_log_by_project_id_and_id(error_log_project_id: int, error_log_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == error_log_project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    error_log = db.query(ErrorLog).filter(ErrorLog.project_id == project.id, ErrorLog.id == error_log_id).first()
    if not error_log:
        raise HTTPException(status_code=404, detail="Error log not found")
    db.delete(error_log)
    db.commit()
    return error_log
