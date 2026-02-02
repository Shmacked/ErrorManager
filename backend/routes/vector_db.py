from fastapi import APIRouter, Depends, UploadFile, File

from backend.services.vector_db import get_vector_db, search_vector_db, add_text_to_vector_db, add_file_to_vector_db
from backend.pydantic_models.vector_db_models import VectorDBInput


router = APIRouter(
    prefix="/vector-db",
    tags=["vector-db"],
)


@router.post("/search")
def search_vector_db_endpoint(vector_db_input: VectorDBInput):
    if vector_db_input.k is None:
        vector_db_input.k = 5
    results = search_vector_db("project_errors", vector_db_input.query, k=vector_db_input.k)
    return results

@router.post("/add")
def add_text_to_vector_db_endpoint(vector_db_input: VectorDBInput):
    results = add_text_to_vector_db("project_errors", vector_db_input.query)
    return results

@router.post("/add/file")
def add_file_to_vector_db_endpoint(file: UploadFile = File(...)):
    results = add_file_to_vector_db("project_errors", file.file.read())
    return results
