from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "clave_super_secreta")
ALGORITHM = "HS256"
AUTH_URL = os.getenv("AUTH_URL", "http://auth:8000/login")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=AUTH_URL)

def verificar_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload  # Contiene 'sub' (usuario) y 'rol'
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
