from langchain_core.tools import tool
from datetime import datetime
from backend.database import get_db
from backend.db_models.db_models import Project
from backend.pydantic_models.project_models import ProjectResponse, ProjectInput, ProjectUpdate
from typing import List, Any
from sqlalchemy import or_


@tool
def calc(num1: int, num2: int, operation: str) -> int:
    """
    Calculates the result of a mathematical operation between two numbers.
    Parameters: num1: int, num2: int, operation: str
    Returns: int
    operation values can be:
    - +
    - -
    - *
    - /
    - %
    """
    if operation == "+":
        return int(num1 + num2)
    elif operation == "-":
        return int(num1 - num2)
    elif operation == "*":
        return int(num1 * num2)
    elif operation == "/":
        return int(num1 / num2)
    elif operation == "%":
        return int(num1 % num2)
    else:
        return int(0)

@tool
def count(data: list[Any]) -> int:
    """
    Counts the number of items in a list.
    Parameters: data: list[Any]
    Returns: int
    """
    return len(data)

@tool
def filter_data(data: list[Any], **kwargs) -> list[Any]:
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
def datetime_to_day_of_week(date_string: str) -> str:
    """
    Convert a datetime string to the day of the week.
    Parameters: date_string: str -> "YYYY-MM-DD HH:MM:SS"
    Returns: str
    """
    # Define the format of your string
    format_str = "%Y-%m-%d %H:%M:%S"

    # Parse the string into a datetime object
    dt_obj = datetime.strptime(date_string, format_str)

    # Convert to POSIX timestamp
    return dt_obj.strftime("%A")

@tool
def datetime_to_unix_timestamp(date_string: str) -> int:
    """
    Convert a datetime string to a Unix timestamp.
    Parameters: date_string: str -> "YYYY-MM-DD HH:MM:SS"
    Returns: int
    """
    # Define the format of your string
    format_str = "%Y-%m-%d %H:%M:%S"

    # Parse the string into a datetime object
    dt_obj = datetime.strptime(date_string, format_str)

    # Convert to POSIX timestamp
    timestamp = dt_obj.timestamp()
    return int(timestamp)

@tool
def current_unix_timestamp() -> int:
    """
    Get the current date and time as a Unix timestamp.
    Returns the current date and time as a Unix timestamp.
    Parameters: None
    Returns: int
    """
    return int(datetime.now().timestamp())

@tool
def get_current_date_time() -> str:
    """
    Get the current date and time.
    Returns the current date and time in the format YYYY-MM-DD HH:MM:SS.

    Parameters: None
    Returns: str
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def get_projects() -> List[ProjectResponse]:
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
def get_project(project_id: int = None, project_uuid: str = None) -> ProjectResponse:
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

@tool(args_schema=ProjectInput)
def create_project(project_input: ProjectInput) -> ProjectResponse:
    """
    Create a new project in the database using the project name and description in the ProjectInput model.
    Returns the newly created project from the database.

    Parameters: ProjectInput
    Returns: ProjectResponse
    """
    db = next(get_db())
    new_project = Project(project_name=project_input.project_name, project_description=project_input.project_description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return ProjectResponse.model_validate(new_project)

@tool(args_schema=ProjectUpdate)
def update_project(project_update: ProjectUpdate) -> ProjectResponse:
    """
    Update a project in the database using the project id or uuid in the ProjectUpdate model. Must specify a project id or uuid in the ProjectUpdate model.
    Returns the updated project from the database.

    Parameters: ProjectUpdate
    Returns: ProjectResponse
    """
    db = next(get_db())
    if project_update.project_id:
        project = db.query(Project).filter(
            or_(
                Project.id == project_update.project_id,
                Project.project_uuid == project_update.project_uuid
            )
        ).first()
        if not project:
            return f"Project with id {project_update.project_id} not found"
    else:
        return "No project id or uuid provided"
    
    for key, value in project_update.model_dump(exclude_unset=True).items():
        setattr(project_update, key, value)

    project_update.project_updated_at = datetime.now()

    db.commit()
    db.refresh(project_update)
    return ProjectResponse.model_validate(project_update)

@tool
def delete_projects(project_ids: List[int] = None, project_uuids: List[str] = None) -> List[ProjectResponse]:
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

