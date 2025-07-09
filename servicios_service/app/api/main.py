from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import Literal, List
from datetime import datetime
import json
import os

app = FastAPI()

# Configuración
DATA_DIR = "archivos_servicios"
os.makedirs(DATA_DIR, exist_ok=True)

# Modelo de datos
class Servicio(BaseModel):
    tipo: Literal["internet", "tv", "telefonia"]
    descripcion: str
    fecha_contratacion: datetime

# Ruta del archivo de servicios por cliente
def ruta_cliente(nombre: str):
    return os.path.join(DATA_DIR, f"{nombre}_servicios.json")

# Registrar nuevo servicio para cliente existente
@app.post("/servicios/{cliente}")
def registrar_servicio(cliente: str, servicio: Servicio):
    ruta = ruta_cliente(cliente)
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            servicios = json.load(f)
    else:
        servicios = []

    servicios.append(servicio.dict())
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(servicios, f, ensure_ascii=False, indent=2)

    return {"mensaje": f"Servicio agregado para cliente {cliente}"}

# Obtener todos los servicios de un cliente
@app.get("/servicios/{cliente}", response_model=List[Servicio])
def obtener_servicios(cliente: str):
    ruta = ruta_cliente(cliente)
    if not os.path.exists(ruta):
        raise HTTPException(status_code=404, detail="El cliente no tiene servicios registrados")
    with open(ruta, "r", encoding="utf-8") as f:
        servicios = json.load(f)
    return servicios

# Listar tipos de servicio disponibles
@app.get("/servicios/")
def tipos_servicio():
    return ["internet", "tv", "telefonia"]
