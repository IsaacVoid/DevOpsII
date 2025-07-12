from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from app.services.auth import verificar_token
import os
import shutil
import boto3
import json

app = FastAPI()

# Configuración
USE_AWS = os.getenv("USE_AWS", "false").lower() == "true"
BUCKET_NAME = os.getenv("BUCKET_NAME", "clientes-bucket")
LOCAL_DIR = "archivos_clientes"

if not USE_AWS:
    os.makedirs(LOCAL_DIR, exist_ok=True)
else:
    s3 = boto3.client("s3")


# POST /archivos: subir nuevo archivo
@app.post("/archivos")
async def subir_archivo(cliente_id: str, archivo: UploadFile = File(...), usuario=Depends(verificar_token)):
    nombre_archivo = f"{cliente_id}_{archivo.filename}"
    if USE_AWS:
        s3.upload_fileobj(archivo.file, BUCKET_NAME, nombre_archivo)
        return {"mensaje": "Archivo subido a S3", "archivo": nombre_archivo}
    else:
        ruta = os.path.join(LOCAL_DIR, nombre_archivo)
        with open(ruta, "wb") as f:
            shutil.copyfileobj(archivo.file, f)
        return {"mensaje": "Archivo guardado localmente", "archivo": nombre_archivo}


# GET /archivos/{id}: obtener archivo
@app.get("/archivos/{archivo_id}")
def obtener_archivo(archivo_id: str, usuario=Depends(verificar_token)):
    if USE_AWS:
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=archivo_id)
            contenido = obj['Body'].read()
            return {"archivo_id": archivo_id, "contenido": contenido.decode()}
        except s3.exceptions.ClientError:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
    else:
        ruta = os.path.join(LOCAL_DIR, archivo_id)
        if not os.path.exists(ruta):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        return FileResponse(ruta, media_type="application/octet-stream", filename=archivo_id)


# GET /clientes/{cliente_id}/archivos: listar archivos de un cliente
@app.get("/clientes/{cliente_id}/archivos")
def listar_archivos_cliente(cliente_id: str, usuario=Depends(verificar_token)):
    if USE_AWS:
        archivos = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' not in archivos:
            return []
        return [obj['Key'] for obj in archivos['Contents'] if obj['Key'].startswith(f"{cliente_id}_")]
    else:
        archivos = os.listdir(LOCAL_DIR)
        return [f for f in archivos if f.startswith(f"{cliente_id}_")]


# PUT /archivos/{archivo_id}: reemplazar archivo existente
@app.put("/archivos/{archivo_id}")
async def reemplazar_archivo(archivo_id: str, nuevo_archivo: UploadFile = File(...), usuario=Depends(verificar_token)):
    if USE_AWS:
        s3.upload_fileobj(nuevo_archivo.file, BUCKET_NAME, archivo_id)
        return {"mensaje": "Archivo reemplazado en S3"}
    else:
        ruta = os.path.join(LOCAL_DIR, archivo_id)
        with open(ruta, "wb") as f:
            shutil.copyfileobj(nuevo_archivo.file, f)
        return {"mensaje": "Archivo reemplazado localmente"}


# DELETE /archivos/{archivo_id}: eliminar archivo
@app.delete("/archivos/{archivo_id}")
def eliminar_archivo(archivo_id: str, usuario=Depends(verificar_token)):
    if USE_AWS:
        try:
            s3.delete_object(Bucket=BUCKET_NAME, Key=archivo_id)
            return {"mensaje": "Archivo eliminado de S3"}
        except s3.exceptions.ClientError:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
    else:
        ruta = os.path.join(LOCAL_DIR, archivo_id)
        if not os.path.exists(ruta):
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        os.remove(ruta)
        return {"mensaje": "Archivo eliminado localmente"}
