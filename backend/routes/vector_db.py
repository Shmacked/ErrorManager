from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from backend.services.vector_db import get_vector_db, search_vector_db, add_text_to_vector_db, add_file_to_vector_db, delete_vector_db, delete_vector_db_data
from backend.pydantic_models.vector_db_models import VectorDBInput, VectorDBDeleteInput


router = APIRouter(
    prefix="/vector-db",
    tags=["vector-db"],
)


@router.post("/search")
async def search_vector_db_endpoint(vector_db_input: VectorDBInput):
    if vector_db_input.k is None:
        vector_db_input.k = 5
    results = search_vector_db("project_errors", vector_db_input.query, k=vector_db_input.k)
    return results

@router.post("/add")
async def add_text_to_vector_db_endpoint(vector_db_input: VectorDBInput):
    results = add_text_to_vector_db("project_errors", vector_db_input.query)
    return results

@router.post("/add/file")
async def add_file_to_vector_db_endpoint(file: UploadFile = File(...)):
    results = add_file_to_vector_db("project_errors", file)
    return results

@router.delete("/delete_collection")
async def delete_vector_db_collection_endpoint(collection_name: str):
    delete_vector_db(collection_name)
    return {"message": f"Vector database {collection_name} deleted successfully"}

@router.delete("/delete_data")
async def delete_vector_db_data_endpoint(collection_name: str, vector_db_delete_input: VectorDBDeleteInput):
    print(vector_db_delete_input)
    results = delete_vector_db_data(collection_name, vector_db_delete_input.data_ids, metadata_filter=vector_db_delete_input.metadata_filter)
    if not results:
        raise HTTPException(status_code=500, detail="Failed to delete vector data.")
    return {"message": f"Vector database {collection_name} data deleted successfully"}
