from pydantic import BaseModel
from typing import Optional

class Producto(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float  # Obligatorio para productos

class Entidad(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None  # No incluye price