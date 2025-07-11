from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
import boto3

app = FastAPI()

# Configuración
USE_AWS = os.getenv("USE_AWS", "false").lower() == "true"
BUCKET_NAME = os.getenv("BUCKET_NAME", "clientes-bucket")
LOCAL_DIR = "archivos_clientes"

if not USE_AWS:
    os.makedirs(LOCAL_DIR, exist_ok=True)
else:
    s3 = boto3.client("s3")

# Modelo de archivo
class ArchivoCliente(BaseModel):
    nombre: str
    contenido: dict

# Crear archivo para cliente
@app.post("/archivo/")
def crear_archivo(data: ArchivoCliente):
    nombre_archivo = f"{data.nombre}.json"

    if USE_AWS:
        try:
            s3.head_object(Bucket=BUCKET_NAME, Key=nombre_archivo)
            raise HTTPException(status_code=400, detail="El archivo ya existe")
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=nombre_archivo,
                    Body=json.dumps(data.contenido),
                    ContentType='application/json'
                )
                return {"mensaje": "Archivo creado en S3"}
            else:
                raise HTTPException(status_code=500, detail="Error de AWS al crear archivo")
    else:
        ruta = os.path.join(LOCAL_DIR, nombre_archivo)
        if os.path.exists(ruta):
            raise HTTPException(status_code=400, detail="El archivo ya existe")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(data.contenido, f)
        return {"mensaje": "Archivo creado localmente"}

# Leer archivo de cliente
@app.get("/archivo/{nombre}")
def obtener_archivo(nombre: str):
    nombre_archivo = f"{nombre}.json"

    if USE_AWS:
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=nombre_archivo)
            return json.loads(obj['Body'].read())
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail="Archivo no encontrado")
            else:
                raise HTTPException(status_code=500, detail="Error al obtener archivo")
    else:
        ruta = os.path.join(LOCAL_DIR, nombre_archivo)
        if not os.path.exists(ruta):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
