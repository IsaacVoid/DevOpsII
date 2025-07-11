from fastapi import FastAPI, HTTPException, Query
import os
import boto3
import json

app = FastAPI()

# Configuración
USE_AWS = os.getenv("USE_AWS", "false").lower() == "true"
BUCKET_NAME = os.getenv("BUCKET_NAME", "clientes-bucket")
LOCAL_DIR = "archivos_clientes"

if USE_AWS:
    s3 = boto3.client("s3")
else:
    os.makedirs(LOCAL_DIR, exist_ok=True)

# Obtener cliente por nombre
@app.get("/consultas/{nombre}")
def consultar_cliente(nombre: str):
    nombre_archivo = f"{nombre}.json"

    if USE_AWS:
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=nombre_archivo)
            return json.loads(obj["Body"].read())
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            else:
                raise HTTPException(status_code=500, detail="Error al acceder a los datos del cliente")
    else:
        ruta = os.path.join(LOCAL_DIR, nombre_archivo)
        if not os.path.exists(ruta):
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)

# Listar todos los clientes
@app.get("/consultas/")
def listar_clientes():
    if USE_AWS:
        try:
            objetos = s3.list_objects_v2(Bucket=BUCKET_NAME)
            if 'Contents' not in objetos:
                return []
            return [obj['Key'].replace('.json', '') for obj in objetos['Contents']]
        except Exception:
            raise HTTPException(status_code=500, detail="No se pudieron listar los clientes")
    else:
        archivos = os.listdir(LOCAL_DIR)
        return [archivo.replace(".json", "") for archivo in archivos if archivo.endswith(".json")]
