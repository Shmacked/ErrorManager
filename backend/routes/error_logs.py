from fastapi import APIRouter, Depends, HTTPException
from pydantic_models.error_models import ErrorLogRequest, ErrorLogResponse, ErrorLogUpdate
from database import get_db
from sqlalchemy.orm import Session


router = APIRouter(
    prefix="/error-logs",
    tags=["error-logs"],
)

@router.get("/")
def get_error_logs():
    return {"message": "Error logs"}

@router.post("/")
def create_error_log(error_log: ErrorLogCreate):
    return {"message": "Error log created"}

@router.get("/{error_log_id}")
def get_error_log(error_log_id: str):
    return {"message": "Error log retrieved"}

@router.put("/{error_log_id}")
def update_error_log(error_log_id: str, error_log: ErrorLogUpdate):
    return {"message": "Error log updated"}

@router.patch("/{error_log_id}")
def patch_error_log(error_log_id: str, error_log: ErrorLogUpdate):
    return {"message": "Error log patched"}

@router.delete("/{error_log_id}")
def delete_error_log(error_log_id: str):
    return {"message": "Error log deleted"}
