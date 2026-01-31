from langchain_core.tools import tool
from datetime import datetime
from backend.database import get_db
from backend.db_models.db_models import Project
from backend.pydantic_models.project_models import ProjectResponse, ProjectCreate, ProjectUpdate
from typing import List, Any


@tool
def count(data: list[Any]):
    """
    Counts the number of items in a list.
    Parameters: data: list[Any]
    Returns: int
    """
    return len(data)

@tool
def filter_data(data: list[Any], **kwargs):
    """
    Filters a list of objects based on the given keyword arguments.
    Parameters: data: list[Any], **kwargs
    Returns: list[Any]
    """
    filtered_data = data
    for k, v in kwargs.items():
        filtered_data = filter(lambda x: getattr(x, k) == v, filtered_data)
    return list(filtered_data)

@tool
def get_current_date_time():
    """
    Get the current date and time.
    Returns the current date and time in the format YYYY-MM-DD HH:MM:SS.

    Parameters: None
    Returns: str
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def get_projects():
    """
    Get all projects from the database.
    Returns a list of projects from the database.

    Parameters: None
    Returns: List[ProjectResponse]
    """
    db = next(get_db())
    projects = db.query(Project).all()
    return [ProjectResponse.model_validate(project) for project in projects]

@tool
def get_project(project_id: int = None, project_uuid: str = None):
    """
    Get a project from the database using the project id or uuid. Must specify a project id or uuid.
    Returns a project from the database.

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
    Create a new project in the database using the project name and description.
    Returns the newly created project from the database.

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
    Update a project in the database using the project id or uuid. Must specify a project id or uuid.
    Returns the updated project from the database.

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
    Delete a project in the database using the project id or uuid. Must specify a project id or uuid.
    Returns a list of deleted projects from the database.

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

