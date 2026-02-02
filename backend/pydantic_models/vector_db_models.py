from pydantic import BaseModel
from typing import Optional, Union

class VectorDBInput(BaseModel):
    query: str
    k: Optional[Union[int, None]] = None

