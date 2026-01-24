from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ProjectInput(BaseModel):
    project_name: str
    project_description: str

# This is the base model for the project
class ProjectBase(BaseModel):
    project_name: str
    project_description: str
    project_created_at: datetime
    project_updated_at: datetime

# This is the model for creating a new project
class ProjectCreate(ProjectBase):
    id: int
    project_uuid: str

# This is the model for updating a project
class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_description: Optional[str] = None

# This is the response model for the project
class ProjectResponse(ProjectCreate):
    # This allows the model to be created from a database model
    model_config = ConfigDict(from_attributes=True)
