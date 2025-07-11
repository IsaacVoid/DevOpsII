from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import Literal, List
from datetime import datetime
from app.services.auth import verificar_token
from fastapi import APIRouter, Depends, HTTPException
from app.services.clientes_api import verificar_cliente
from app.domain.schemas import Servicio
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
async def registrar_servicio(cliente: str, servicio: Servicio, usuario=Depends(verificar_token)):
    existe = await verificar_cliente(cliente)
    if not existe:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    # Aquí va tu lógica actual de registrar el servicio
    return {"mensaje": f"Servicio registrado para {cliente}"}


# Obtener todos los servicios de un cliente
@app.get("/servicios/{cliente}")
def consultar_servicios(cliente: str, usuario=Depends(verificar_token)):
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

