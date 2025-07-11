from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

# Configuración JWT
SECRET_KEY = "clave_super_secreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Usuarios de prueba (en memoria)
usuarios = {
    "admin": {"username": "admin", "password": "admin123", "rol": "administrador"},
    "it": {"username": "it", "password": "it123", "rol": "it"},
    "soporte": {"username": "soporte", "password": "soporte123", "rol": "atencion"}
}

# App FastAPI
app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Funciones JWT

def crear_token(datos: dict, expires_delta: Optional[timedelta] = None):
    to_encode = datos.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

# Endpoint: Login
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    usuario = usuarios.get(form_data.username)
    if not usuario or usuario["password"] != form_data.password:
        raise HTTPException(status_code=400, detail="Credenciales inválidas")

    token_data = {"sub": usuario["username"], "rol": usuario["rol"]}
    access_token = crear_token(token_data, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))

    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint protegido de prueba
@app.get("/protegido")
def protegido(token: str = Depends(oauth2_scheme)):
    payload = verificar_token(token)
    return {"mensaje": f"Acceso autorizado para {payload['sub']} con rol {payload['rol']}"}
