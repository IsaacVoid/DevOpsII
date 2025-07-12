from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import json

from app.services.auth import verificar_token

app = FastAPI()

USE_AWS = os.getenv("USE_AWS", "false").lower() == "true"
BUCKET_NAME = os.getenv("BUCKET_NAME", "consultas-bucket")
LOCAL_DIR = "consultas_logs"

if USE_AWS:
    import boto3
    s3 = boto3.client("s3")
else:
    os.makedirs(LOCAL_DIR, exist_ok=True)

class Consulta(BaseModel):
    usuario_id: str
    cliente_id: str
    accion: str
    timestamp: Optional[str] = None

@app.post("/consultas")
def registrar_consulta(consulta: Consulta, usuario=Depends(verificar_token)):
    consulta.timestamp = datetime.utcnow().isoformat()
    registro = consulta.dict()

    if USE_AWS:
        key = f"{registro['timestamp']}_{registro['usuario_id']}_{registro['cliente_id']}.json"
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=json.dumps(registro), ContentType='application/json')
        return {"mensaje": "Consulta registrada en S3"}
    else:
        filename = f"{registro['timestamp']}_{registro['usuario_id']}_{registro['cliente_id']}.json"
        ruta = os.path.join(LOCAL_DIR, filename)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(registro, f)
        return {"mensaje": "Consulta registrada localmente"}

@app.get("/consultas", response_model=List[Consulta])
def obtener_historial(usuario_id: Optional[str] = None, cliente_id: Optional[str] = None, usuario=Depends(verificar_token)):
    resultados = []

    if USE_AWS:
        objetos = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' not in objetos:
            return []
        for obj in objetos['Contents']:
            data = s3.get_object(Bucket=BUCKET_NAME, Key=obj['Key'])
            consulta = json.loads(data['Body'].read())
            if (usuario_id and consulta['usuario_id'] != usuario_id) or (cliente_id and consulta['cliente_id'] != cliente_id):
                continue
            resultados.append(consulta)
    else:
        archivos = os.listdir(LOCAL_DIR)
        for archivo in archivos:
            with open(os.path.join(LOCAL_DIR, archivo), "r", encoding="utf-8") as f:
                consulta = json.load(f)
                if (usuario_id and consulta['usuario_id'] != usuario_id) or (cliente_id and consulta['cliente_id'] != cliente_id):
                    continue
                resultados.append(consulta)

    return resultados
