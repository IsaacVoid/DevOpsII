from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.domain.models import Base, Usuario
from passlib.context import CryptContext
import os

app = FastAPI()

# Configuración
SECRET_KEY = os.getenv("SECRET_KEY", "clave_super_secreta")
ALGORITHM = "HS256"
DB_URL = os.getenv("DATABASE_URL", "sqlite:///./usuarios.db")

# DB
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base.metadata.create_all(bind=engine)

# Seguridad
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Registro de usuario
@app.post("/register")
def registrar_usuario(
    username: str = Form(...),
    password: str = Form(...),
    rol: str = Form(...)
):
    db = SessionLocal()
    if db.query(Usuario).filter_by(username=username).first():
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    usuario = Usuario(
        username=username,
        password=pwd_context.hash(password),
        rol=rol
    )
    db.add(usuario)
    db.commit()
    db.close()
    return {"mensaje": "Usuario registrado correctamente"}

# Login
@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...)
):
    db = SessionLocal()
    usuario = db.query(Usuario).filter_by(username=username).first()
    if not usuario or not pwd_context.verify(password, usuario.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    token_data = {"sub": usuario.username, "rol": usuario.rol}
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    db.close()
    return {"access_token": token, "token_type": "bearer"}

# Verificación (opcional para otros servicios)
@app.get("/me")
def leer_usuario_actual(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
