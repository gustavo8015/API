from pydantic import BaseModel
from typing import Optional
from bson import ObjectId

class Entidad(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}