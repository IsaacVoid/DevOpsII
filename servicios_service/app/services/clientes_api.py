import httpx
import os

CLIENTES_URL = os.getenv("CLIENTES_URL", "http://clientes:8000")

async def verificar_cliente(nombre: str) -> bool:
    url = f"{CLIENTES_URL}/clientes/{nombre}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
        return response.status_code == 200
    except httpx.RequestError:
        return False
