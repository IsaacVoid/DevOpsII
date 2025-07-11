from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import uuid
import datetime
import os
import json

app = FastAPI()

MEJORAS_FILE = "mejoras_sugeridas.json"
VERSIONES_FILE = "historial_versiones.json"
os.makedirs("data", exist_ok=True)
MEJORAS_PATH = os.path.join("data", MEJORAS_FILE)
VERSIONES_PATH = os.path.join("data", VERSIONES_FILE)

# Modelos
class Mejora(BaseModel):
    id: str = None
    fecha: str = None
    sugerido_por: str
    descripcion: str
    estado: str = "pendiente"  # pendiente, aceptada, rechazada

class Version(BaseModel):
    numero: str
    descripcion: str
    fecha: str = None
    cambios: List[str]

# Funciones auxiliares

def cargar_lista(ruta):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def guardar_lista(ruta, lista):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2)

# Endpoints

@app.post("/mejoras/")
def sugerir_mejora(mejora: Mejora):
    mejora.id = str(uuid.uuid4())
    mejora.fecha = datetime.datetime.now().isoformat()
    mejoras = cargar_lista(MEJORAS_PATH)
    mejoras.append(mejora.model_dump())
    guardar_lista(MEJORAS_PATH, mejoras)
    return {"mensaje": "Mejora registrada", "id": mejora.id}

@app.get("/mejoras/")
def listar_mejoras():
    return cargar_lista(MEJORAS_PATH)

@app.put("/mejoras/{id}")
def actualizar_estado_mejora(id: str, nuevo_estado: str):
    mejoras = cargar_lista(MEJORAS_PATH)
    for mejora in mejoras:
        if mejora["id"] == id:
            mejora["estado"] = nuevo_estado
            guardar_lista(MEJORAS_PATH, mejoras)
            return {"mensaje": "Estado actualizado"}
    raise HTTPException(status_code=404, detail="Mejora no encontrada")

@app.post("/versiones/")
def agregar_version(version: Version):
    version.fecha = datetime.datetime.now().isoformat()
    versiones = cargar_lista(VERSIONES_PATH)
    versiones.append(version.model_dump())
    guardar_lista(VERSIONES_PATH, versiones)
    return {"mensaje": "Versión registrada"}

@app.get("/versiones/")
def listar_versiones():
    return cargar_lista(VERSIONES_PATH)
