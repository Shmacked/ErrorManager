from langchain_core.tools import tool
from datetime import datetime
from backend.database import get_db
from backend.db_models.db_models import Project
from backend.pydantic_models.project_models import ProjectResponse, ProjectCreate, ProjectUpdate
from typing import List

@tool
def get_current_date_time():
    """
    Get the current date and time
    Returns the current date and time in the format YYYY-MM-DD HH:MM:SS

    Parameters: None
    Returns: str
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def get_projects():
    """
    Get the projects
    Returns a list of projects

    Parameters: None
    Returns: List[ProjectResponse]
    """
    db = next(get_db())
    projects = db.query(Project).all()
    return [ProjectResponse.model_validate(project) for project in projects]

@tool
def get_project(project_id: int = None, project_uuid: str = None):
    """
    Get a project using the project id or uuid. Must specify a project id or uuid.
    Returns a project

    Parameters: project_id: int = None, project_uuid: str = None
    Returns: ProjectResponse
    """
    db = next(get_db())
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
    elif project_uuid:
        project = db.query(Project).filter(Project.project_uuid == project_uuid).first()
    else:
        return "No project id or uuid provided"
    return ProjectResponse.model_validate(project)

@tool
def create_project(project_name: str, project_description: str):
    """
    Create a new project
    Returns the newly created project

    Parameters: project_name: str, project_description: str
    Returns: ProjectResponse
    """
    db = next(get_db())
    new_project = Project(project_name=project_name, project_description=project_description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return ProjectResponse.model_validate(new_project)

@tool
def update_project(project_id: int = None, project_uuid: str = None, project_name: str = None, project_description: str = None):
    """
    Update a project using the project id or uuid. Must specify a project id or uuid.
    Returns the updated project

    Parameters: project_id: int = None, project_uuid: str = None, project_name: str = None, project_description: str = None
    Returns: ProjectResponse
    """
    db = next(get_db())
    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return f"Project with id {project_id} not found"
    elif project_uuid:
        project = db.query(Project).filter(Project.project_uuid == project_uuid).first()
        if not project:
            return f"Project with uuid {project_uuid} not found"
    else:
        return "No project id or uuid provided"
    
    for key, value in project.model_dump(exclude_unset=True).items():
        setattr(project, key, value)

    project.project_updated_at = datetime.now()

    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)

@tool
def delete_projects(project_ids: List[int] = None, project_uuids: List[str] = None):
    """
    Delete a project using the project id or uuid. Must specify a project id or uuid.
    Returns a list of deleted projects

    Parameters: project_ids: List[int] = None, project_uuids: List[str] = None
    Returns: List[ProjectResponse]
    """
    db = next(get_db())
    if project_ids:
        projects = db.query(Project).filter(Project.id.in_(project_ids)).all()
    elif project_uuids:
        projects = db.query(Project).filter(Project.project_uuid.in_(project_uuids)).all()
    else:
        return "No project ids or uuids provided"
    for project in projects:
        db.delete(project)
    db.commit()
    return [ProjectResponse.model_validate(project) for project in projects]

