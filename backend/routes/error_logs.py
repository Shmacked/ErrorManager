from fastapi import APIRouter, Depends, HTTPException


router = APIRouter(
    prefix="/error-logs",
    tags=["error-logs"],
)

@router.get("/")
def get_error_logs():
    return {"message": "Error logs"}
