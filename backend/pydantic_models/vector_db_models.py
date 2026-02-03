from pydantic import BaseModel
from typing import Optional, Union, Dict, Any

class VectorDBInput(BaseModel):
    query: str
    k: Optional[Union[int, None]] = None


class VectorDBDeleteInput(BaseModel):
    data_ids: Optional[list[int]] = None
    metadata_filter: Optional[Dict[str, Any]] = None
