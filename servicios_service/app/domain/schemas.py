from pydantic import BaseModel

class Servicio(BaseModel):
    tipo: str
    descripcion: str
