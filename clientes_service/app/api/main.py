from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import json
import os
import boto3

app = FastAPI()

# Configuración
USE_AWS = os.getenv("USE_AWS", "false").lower() == "true"
BUCKET_NAME = os.getenv("BUCKET_NAME", "clientes-bucket")
LOCAL_BUCKET = "archivos_clientes"

if not USE_AWS:
    os.makedirs(LOCAL_BUCKET, exist_ok=True)
else:
    s3 = boto3.client("s3")

# Modelos de datos
class Direccion(BaseModel):
    calle: str
    numero: str
    ciudad: str
    estado: str

class Cliente(BaseModel):
    nombre: str
    tipo: str  # "persona" o "negocio"
    direccion: Direccion
    telefono: str
    email: str

# Crear cliente
@app.post("/clientes/")
def crear_cliente(cliente: Cliente):
    nombre_archivo = f"{cliente.nombre}.json"

    if USE_AWS:
        try:
            s3.head_object(Bucket=BUCKET_NAME, Key=nombre_archivo)
            raise HTTPException(status_code=400, detail="El cliente ya existe")
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=nombre_archivo,
                    Body=cliente.json(),
                    ContentType='application/json'
                )
                return {"mensaje": "Cliente creado exitosamente"}
            else:
                raise HTTPException(status_code=500, detail="Error al verificar el cliente")
    else:
        ruta = os.path.join(LOCAL_BUCKET, nombre_archivo)
        if os.path.exists(ruta):
            raise HTTPException(status_code=400, detail="El cliente ya existe")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(cliente.json())
        return {"mensaje": "Cliente creado exitosamente"}

# Agregar servicio
@app.put("/clientes/{nombre}/servicio")
def agregar_servicio(nombre: str, descripcion: str = Query(...)):
    nombre_archivo = f"{nombre}.json"

    if USE_AWS:
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=nombre_archivo)
            cliente_data = json.loads(obj["Body"].read())

            servicios = cliente_data.get("servicios", [])
            servicios.append(descripcion)
            cliente_data["servicios"] = servicios

            s3.put_object(
                Bucket=BUCKET_NAME,
                Key=nombre_archivo,
                Body=json.dumps(cliente_data),
                ContentType='application/json'
            )
            return {"mensaje": "Servicio agregado correctamente"}

        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            else:
                raise HTTPException(status_code=500, detail="Error al acceder al archivo del cliente")
    else:
        ruta = os.path.join(LOCAL_BUCKET, nombre_archivo)
        if not os.path.exists(ruta):
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        with open(ruta, "r+", encoding="utf-8") as f:
            cliente_data = json.load(f)
            servicios = cliente_data.get("servicios", [])
            servicios.append(descripcion)
            cliente_data["servicios"] = servicios
            f.seek(0)
            f.write(json.dumps(cliente_data))
            f.truncate()
        return {"mensaje": "Servicio agregado correctamente"}

# Obtener cliente
@app.get("/clientes/{nombre}")
def obtener_cliente(nombre: str):
    nombre_archivo = f"{nombre}.json"

    if USE_AWS:
        try:
            obj = s3.get_object(Bucket=BUCKET_NAME, Key=nombre_archivo)
            contenido = obj["Body"].read()
            return json.loads(contenido)
        except s3.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise HTTPException(status_code=404, detail="Cliente no encontrado")
            else:
                raise HTTPException(status_code=500, detail="Error al acceder a los datos del cliente")
    else:
        ruta = os.path.join(LOCAL_BUCKET, nombre_archivo)
        if not os.path.exists(ruta):
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)

# Listar clientes
@app.get("/clientes/")
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
        archivos = os.listdir(LOCAL_BUCKET)
        return [archivo.replace(".json", "") for archivo in archivos if archivo.endswith(".json")]
