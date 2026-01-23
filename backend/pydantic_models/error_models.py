from pydantic import BaseModel, Field, Optional
import uuid

# This is the input model for the error log from the user
# This gets passed to the LLM for parsing
class ErrorInput(BaseModel):
    project_id: int
    error_message: str

# This is the base model for the error log
# This is used to validate the error log response from the LLM
class ErrorLogBase(BaseModel):
    error_type: str # The type of error
    error_message: str # The message of the error
    source: str # The source file of the error
    line_number: int # The line number of the error
    traceback: str # The traceback of the error

# This is the response model for the error log from the LLM after it gets added to the database
class ErrorLogResponse(ErrorLogBase):
    id: int
    project_id: int
    log_id: str
    created_timestamp: str
    status: str

# This is the model for updating the error log in the database
class ErrorLogUpdate(BaseModel):
    id: Optional[int] = None
    project_id: int # this is the project id foreign key
    log_id: Optional[str] = None
    status: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    source: Optional[str] = None
    line_number: Optional[int] = None
    traceback: Optional[str] = None

# This is the base model for the project
class ProjectBase(BaseModel):
    project_name: str
    project_description: str
    project_created_at: str
    project_updated_at: str

# This is the model for creating a new project
class ProjectCreate(ProjectBase):
    id: int
    project_uuid: str

# This is the model for updating a project
class ProjectUpdate(ProjectBase):
    id: Optional[int] = None
    project_uuid: Optional[str] = None
    project_name: Optional[str] = None
    project_description: Optional[str] = None
