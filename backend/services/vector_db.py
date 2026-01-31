from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from typing import Any, List, Optional, Dict
from pathlib import Path
from datetime import datetime
from io import BytesIO
import hashlib
import spacy


load_dotenv(dotenv_path="backend/.env")

PERSISTENT_DIRECTORY = "backend/chroma_store"
COLLECTION_NAME = "project_errors" # What tkind of data we're storing
EMBEDDING = OpenAIEmbeddings(model="text-embedding-3-small")

vector_dbs = {
    COLLECTION_NAME: Chroma(persist_directory=PERSISTENT_DIRECTORY, embedding_function=EMBEDDING, collection_name=COLLECTION_NAME)
}

def get_vector_db(collection_name: str):
    """
    Get a vector database.
    """
    collection = vector_dbs.get(collection_name)
    if not collection:
        raise ValueError(f"Vector database {collection_name} not found")
    return collection

def delete_vector_db(collection_name: str) -> None:
    collection = get_vector_db(collection_name)
    collection.delete_collection()
    if collection_name in vector_dbs:
        del vector_dbs[collection_name]

def add_documents_to_db(collection_name: str, docs: List[Document]) -> int:
    collection = get_vector_db(collection_name)
    
    # Chunk the documents properly
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(docs)
    
    collection.add_documents(split_docs)
    collection.persist()
    return len(split_docs)

def add_text_to_vector_db(collection_name: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> int:
    # Wrap raw text into a Document object
    if metadata is None:
        metadata = {}

    metadata["created_timestamp"] = int(datetime.now().timestamp()) # Unix timestamp

    doc = Document(page_content=text, metadata=metadata)
    return add_documents_to_db(collection_name, [doc])

def add_file_to_vector_db(collection_name: str, file_as_bytes: bytes, metadata: Optional[Dict[str, Any]] = None) -> int:
    # Note: Since Unstructured is giving you trouble, make sure 
    # you've switched to a working loader like PyPDF or similar if needed.
    loader = UnstructuredFileLoader(BytesIO(file_as_bytes))
    docs = loader.load()
    
    # Merge custom metadata into the loaded docs if provided
    if metadata:
        for doc in docs:
            doc.metadata.update(metadata)
    
    metadata["created_timestamp"] = int(datetime.now().timestamp()) # Unix timestamp
            
    return add_documents_to_db(collection_name, docs)

def search_vector_db(collection_name: str, query: str, k: int = 5) -> List[Document]:
    collection = get_vector_db(collection_name)
    return collection.similarity_search(query, k=k)

def extract_entities(text: str) -> List[str]:
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    return [ent.text for ent in doc.ents]
