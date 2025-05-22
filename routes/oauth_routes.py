from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from services.oauth_service import oauth_service, OAuthServiceError
from auth import generate_tokens
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["oauth"])

@router.get("/{provider}/login")
async def oauth_login(provider: str):
    """Inicia el proceso de autenticación OAuth con un proveedor."""
    try:
        auth_url = oauth_service.get_authorization_url(provider)
        return {"auth_url": auth_url}
    except OAuthServiceError as e:
        logger.error(f"Error en OAuth login para {provider}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error inesperado en OAuth login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(..., description="Código de autorización"),
    state: str = Query(..., description="Estado de la solicitud"),
    error: str = Query(None, description="Error de OAuth")
):
    """Maneja el callback de OAuth y completa la autenticación."""
    try:
        # Verificar si hay error en la respuesta
        if error:
            logger.error(f"Error OAuth desde {provider}: {error}")
            return RedirectResponse(
                url=f"http://localhost:8000/api/cliente-api?oauth_error={error}",
                status_code=302
            )
        
        # Intercambiar código por token
        token_info = oauth_service.exchange_code_for_token(provider, code, state)
        
        # Obtener información del usuario
        user_info = oauth_service.get_user_info(provider, token_info['access_token'])
        
        # Crear o actualizar usuario en la base de datos
        user = await oauth_service.create_or_update_user(user_info)
        
        # Generar tokens JWT para la sesión
        tokens = await generate_tokens(user['email'])
        
        # Redirigir a la aplicación con tokens
        redirect_url = (
            f"http://localhost:8000/api/cliente-api"
            f"?oauth_success=true"
            f"&access_token={tokens.access_token}"
            f"&refresh_token={tokens.refresh_token}"
            f"&provider={provider}"
            f"&user_name={user_info['name']}"
        )
        
        return RedirectResponse(url=redirect_url, status_code=302)
        
    except OAuthServiceError as e:
        logger.error(f"Error en OAuth callback para {provider}: {str(e)}")
        return RedirectResponse(
            url=f"http://localhost:8000/api/cliente-api?oauth_error={str(e)}",
            status_code=302
        )
    except Exception as e:
        logger.error(f"Error inesperado en OAuth callback: {str(e)}")
        return RedirectResponse(
            url=f"http://localhost:8000/api/cliente-api?oauth_error=Error interno del servidor",
            status_code=302
        )

@router.get("/providers")
async def get_oauth_providers():
    """Obtiene la lista de proveedores OAuth disponibles."""
    try:
        providers = []
        for provider_name in oauth_service.providers.keys():
            providers.append({
                "name": provider_name,
                "display_name": provider_name.capitalize(),
                "login_url": f"/auth/{provider_name}/login"
            })
        
        return {"providers": providers}
    except Exception as e:
        logger.error(f"Error al obtener proveedores OAuth: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.post("/unlink/{provider}")
async def unlink_oauth_provider(provider: str, request: Request):
    """Desvincula un proveedor OAuth de la cuenta del usuario."""
    try:
        # Aquí implementarías la lógica para desvincular el proveedor
        # Necesitarías obtener el usuario actual de la sesión
        
        # Por ahora, solo retornamos un mensaje de éxito
        return {"message": f"Proveedor {provider} desvinculado exitosamente"}
    except Exception as e:
        logger.error(f"Error al desvincular proveedor {provider}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/user/connected-accounts")
async def get_connected_accounts(request: Request):
    """Obtiene las cuentas OAuth vinculadas al usuario actual."""
    try:
        # Aquí implementarías la lógica para obtener las cuentas vinculadas
        # Necesitarías obtener el usuario actual de la sesión
        
        # Por ahora, retornamos un ejemplo
        connected_accounts = []
        for provider in oauth_service.providers.keys():
            connected_accounts.append({
                "provider": provider,
                "connected": False,  # Implementar lógica real
                "user_name": "",
                "email": ""
            })
        
        return {"connected_accounts": connected_accounts}
    except Exception as e:
        logger.error(f"Error al obtener cuentas conectadas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")