from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from database import Base
from uuid import uuid4


class ErrorLog(Base):
    __tablename__ = "error_logs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    log_id = Column(String, unique=True, default=lambda: str(uuid4())) # Short UUID string
    created_timestamp = Column(DateTime, default=datetime.now) # UTC timezone
    status = Column(String) # "pending", "resolved", "ignored"
    error_type = Column(String) # The type of error
    error_message = Column(String) # The message of the error
    source = Column(String) # The source file of the error
    line_number = Column(Integer) # The line number of the error
    traceback = Column(String) # The traceback of the error


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    project_uuid = Column(String, unique=True, default=lambda: str(uuid4())) # Short UUID string
    project_name = Column(String)
    project_description = Column(String)
    project_created_at = Column(DateTime, default=datetime.now) # UTC timezone
    project_updated_at = Column(DateTime, default=datetime.now) # UTC timezone
