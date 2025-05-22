import os
import requests
import secrets
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from fastapi import HTTPException
from db.database import database
from auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OAuthServiceError(Exception):
    """Excepción personalizada para errores en el servicio OAuth."""
    pass

class OAuthService:
    def __init__(self):
        # Configuración de OAuth para diferentes proveedores
        self.providers = {
    'google': {
        'client_id': '1093869804938-jp8dplodvgk3mm8inbsfcbr8oh11rpln.apps.googleusercontent.com',  # ← Cambiar por el real
        'client_secret': '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',  # ← Cambiar por el real
        'redirect_uri': 'http://localhost:8000/auth/google/callback',
        'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'user_info_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
        'scope': 'openid email profile'
    },
    'github': {
        'client_id': 'tu-github-client-id',
        'client_secret': 'tu-github-client-secret',
        'redirect_uri': 'http://localhost:8000/auth/github/callback',
        'auth_url': 'https://github.com/login/oauth/authorize',
        'token_url': 'https://github.com/login/oauth/access_token',
        'user_info_url': 'https://api.github.com/user',
        'scope': 'user:email'
    },
    'facebook': {
        'client_id': 'tu-facebook-client-id',
        'client_secret': 'tu-facebook-client-secret',
        'redirect_uri': 'http://localhost:8000/auth/facebook/callback',
        'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
        'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
        'user_info_url': 'https://graph.facebook.com/me',
        'scope': 'email'
    },
    'microsoft': {
        'client_id': 'tu-microsoft-client-id',
        'client_secret': 'tu-microsoft-client-secret',
        'redirect_uri': 'http://localhost:8000/auth/microsoft/callback',
        'auth_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
        'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
        'user_info_url': 'https://graph.microsoft.com/v1.0/me',
        'scope': 'openid email profile'
    }
}
        
        
        # Store para estados OAuth (en producción usar Redis o similar)
        self.state_store = {}

    def get_authorization_url(self, provider: str) -> str:
        """Genera la URL de autorización para un proveedor OAuth."""
        if provider not in self.providers:
            raise OAuthServiceError(f"Proveedor '{provider}' no soportado")
        
        config = self.providers[provider]
        state = secrets.token_urlsafe(32)
        
        # Guardar estado para validación posterior
        self.state_store[state] = {
            'provider': provider,
            'timestamp': requests.utils.default_user_agent()
        }
        
        params = {
            'client_id': config['client_id'],
            'redirect_uri': config['redirect_uri'],
            'scope': config['scope'],
            'response_type': 'code',
            'state': state
        }
        
        # Parámetros específicos por proveedor
        if provider == 'microsoft':
            params['response_mode'] = 'query'
        
        auth_url = f"{config['auth_url']}?{urlencode(params)}"
        logger.info(f"URL de autorización generada para {provider}: {auth_url}")
        
        return auth_url

    def exchange_code_for_token(self, provider: str, code: str, state: str) -> Dict[str, Any]:
        """Intercambia el código de autorización por un token de acceso."""
        if provider not in self.providers:
            raise OAuthServiceError(f"Proveedor '{provider}' no soportado")
        
        # Validar estado
        if state not in self.state_store:
            raise OAuthServiceError("Estado OAuth inválido")
        
        if self.state_store[state]['provider'] != provider:
            raise OAuthServiceError("Estado OAuth no coincide con el proveedor")
        
        # Limpiar estado usado
        del self.state_store[state]
        
        config = self.providers[provider]
        
        token_data = {
            'client_id': config['client_id'],
            'client_secret': config['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': config['redirect_uri']
        }
        
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # GitHub requiere header específico
        if provider == 'github':
            headers['Accept'] = 'application/json'
        
        try:
            response = requests.post(
                config['token_url'],
                data=token_data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            token_info = response.json()
            
            if 'access_token' not in token_info:
                raise OAuthServiceError("No se recibió access_token")
            
            logger.info(f"Token obtenido exitosamente para {provider}")
            return token_info
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener token para {provider}: {str(e)}")
            raise OAuthServiceError(f"Error al obtener token: {str(e)}")

    def get_user_info(self, provider: str, access_token: str) -> Dict[str, Any]:
        """Obtiene información del usuario usando el token de acceso."""
        if provider not in self.providers:
            raise OAuthServiceError(f"Proveedor '{provider}' no soportado")
        
        config = self.providers[provider]
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        # Parámetros específicos por proveedor
        params = {}
        if provider == 'facebook':
            params['fields'] = 'id,name,email,picture'
        
        try:
            response = requests.get(
                config['user_info_url'],
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            user_info = response.json()
            
            # Normalizar datos de usuario según el proveedor
            normalized_user = self._normalize_user_data(provider, user_info)
            
            logger.info(f"Información de usuario obtenida para {provider}: {normalized_user['email']}")
            return normalized_user
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener información de usuario para {provider}: {str(e)}")
            raise OAuthServiceError(f"Error al obtener información de usuario: {str(e)}")

    def _normalize_user_data(self, provider: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza los datos de usuario según el proveedor."""
        normalized = {
            'provider': provider,
            'provider_id': str(user_data.get('id', '')),
            'email': '',
            'name': '',
            'picture': '',
            'raw_data': user_data
        }
        
        if provider == 'google':
            normalized.update({
                'email': user_data.get('email', ''),
                'name': user_data.get('name', ''),
                'picture': user_data.get('picture', ''),
                'provider_id': str(user_data.get('id', ''))
            })
        elif provider == 'github':
            normalized.update({
                'email': user_data.get('email', ''),
                'name': user_data.get('name') or user_data.get('login', ''),
                'picture': user_data.get('avatar_url', ''),
                'provider_id': str(user_data.get('id', ''))
            })
        elif provider == 'facebook':
            normalized.update({
                'email': user_data.get('email', ''),
                'name': user_data.get('name', ''),
                'picture': user_data.get('picture', {}).get('data', {}).get('url', ''),
                'provider_id': str(user_data.get('id', ''))
            })
        elif provider == 'microsoft':
            normalized.update({
                'email': user_data.get('mail') or user_data.get('userPrincipalName', ''),
                'name': user_data.get('displayName', ''),
                'picture': '',  # Microsoft Graph requiere llamada adicional para foto
                'provider_id': str(user_data.get('id', ''))
            })
        
        return normalized

    async def create_or_update_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea o actualiza un usuario en la base de datos."""
        try:
            email = user_data['email']
            provider = user_data['provider']
            provider_id = user_data['provider_id']
            
            if not email:
                raise OAuthServiceError("El email es requerido")
            
            # Buscar usuario existente por email
            existing_user = database["users"].find_one({"email": email})
            
            if existing_user:
                # Actualizar usuario existente con información OAuth
                update_data = {
                    f"oauth_{provider}": {
                        'provider_id': provider_id,
                        'name': user_data['name'],
                        'picture': user_data['picture'],
                        'last_login': requests.utils.default_user_agent()
                    }
                }
                
                database["users"].update_one(
                    {"email": email},
                    {"$set": update_data}
                )
                
                logger.info(f"Usuario actualizado con OAuth {provider}: {email}")
                return existing_user
            else:
                # Crear nuevo usuario
                new_user = {
                    "email": email,
                    "hashed_password": get_password_hash(secrets.token_urlsafe(32)),  # Password temporal
                    "disabled": False,
                    "created_via": f"oauth_{provider}",
                    "name": user_data['name'],
                    "picture": user_data['picture'],
                    f"oauth_{provider}": {
                        'provider_id': provider_id,
                        'name': user_data['name'],
                        'picture': user_data['picture'],
                        'last_login': requests.utils.default_user_agent()
                    }
                }
                
                result = database["users"].insert_one(new_user)
                new_user["_id"] = result.inserted_id
                
                logger.info(f"Nuevo usuario creado con OAuth {provider}: {email}")
                return new_user
                
        except Exception as e:
            logger.error(f"Error al crear/actualizar usuario OAuth: {str(e)}")
            raise OAuthServiceError(f"Error al crear/actualizar usuario: {str(e)}")

# Instancia global del servicio OAuth
oauth_service = OAuthService()