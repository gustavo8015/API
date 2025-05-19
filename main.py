from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from db.database import database
from routes.producto_routes import router as producto_router
from routes.entidad_routes import router as entidad_router
from routes.scraping_routes import router as scraping_router
from auth import UserInDB, authenticate_user, generate_tokens, get_current_active_user, OAuth2PasswordRequestForm, get_password_hash, Token, RefreshTokenRequest, decode_token
from datetime import timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(producto_router)
app.include_router(entidad_router)
app.include_router(scraping_router)

# Modelo para los datos de registro
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

# Endpoint de registro
@app.post("/register")
async def register_user(request: RegisterRequest):
    email = request.email
    password = request.password
    logger.info(f"Intento de registro con email: {email}")
    if database["users"].find_one({"email": email}):
        logger.warning(f"El email {email} ya está registrado")
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    
    hashed_password = get_password_hash(password)
    user = {"email": email, "hashed_password": hashed_password, "disabled": False}
    result = database["users"].insert_one(user)
    logger.info(f"Usuario registrado con ID: {result.inserted_id}")
    return {"mensaje": "Usuario registrado exitosamente"}

# Endpoint de login
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        logger.info(f"Intento de login con email: {form_data.username}")
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            logger.warning(f"Credenciales incorrectas para email: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        tokens = await generate_tokens(user.email)
        logger.info(f"Tokens generados para {user.email}")
        return tokens
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error interno en login para {form_data.username}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al autenticar usuario")

# Endpoint para renovar tokens
@app.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    try:
        payload = decode_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: se esperaba un refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: no se encontró el usuario",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user = await get_user(email)
        if not user or user.disabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado o inactivo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        tokens = await generate_tokens(email)
        logger.info(f"Tokens renovados para {email}")
        return tokens
    except Exception as e:
        logger.error(f"Error al renovar token: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno al renovar token")

@app.get("/users/me")
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    return {"email": current_user.email}

@app.get("/api/cliente-api", response_class=HTMLResponse)
async def serve_cliente_api():
    html_path = Path(__file__).parent / "cliente-api.html"
    if not html_path.is_file():
        raise HTTPException(status_code=404, detail="cliente-api.html not found")
    return FileResponse(html_path)

# Endpoint raíz modificado para redirigir
@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(url="/api/cliente-api")

@app.get("/test")
async def test_route():
    logger.info("Accediendo a la ruta de prueba /test")
    return {"message": "Ruta de prueba funcionando"}