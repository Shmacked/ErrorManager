from pydantic import BaseModel, ConfigDict
from typing import Optional

# This is the input model for the error log from the user
# This gets passed to the LLM for parsing
class ErrorLogInput(BaseModel):
    project_id: int
    traceback: str

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

    # This allows the model to be created from a database model
    model_config = ConfigDict(from_attributes=True)

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
