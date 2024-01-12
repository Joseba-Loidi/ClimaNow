import json
from fastapi import Body, FastAPI, Form, Query, Request, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordBearer

import httpx, os
from pydantic import BaseModel
from typing import Optional
from fastapi import FastAPI
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError, PyJWTError
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# Retrieve environment variables with default values
WEATHER_SERVICE_URL = os.getenv('WEATHER_SERVICE_URL', 'http://localhost:8000/weather')
AUTH_SERVICE_URL = os.getenv('AUTH_SERVICE_URL', 'http://localhost:3000/api/user')

tags_metadata = [
    {
        "name": "users",
        "description": "Operations with users. The **login**, **logout**, **user-profile** and **register** logic is here.",
    },
    {
        "name": "weather",
        "description": "Operations related to weather information. Retrieve current weather conditions for a specific city.",
    },
]

app = FastAPI(openapi_tags=tags_metadata)
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount the static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Redirect root to index.html
@app.get("/")
async def read_root():
    return RedirectResponse(url="/static/index.html")

client = httpx.Client()

# Models for user authentication
class UserRegister(BaseModel):
    username: str
    password: str
    mail: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserToken(BaseModel):
    token: str

class WeatherResponse(BaseModel):
    temperature: float
    description: str
    city: str
    latitude: float
    longitude: float
    feels_like: float

class FavoritesRequest(BaseModel):
    token: str
    location: str

# Authentication endpoints
@app.post("/auth/register", tags=["users"], status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister):
    print(f"{AUTH_SERVICE_URL}/auth/register*************")
    response = client.post(f"{AUTH_SERVICE_URL}/register", json=user.dict())
    print(response)

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already registered")

    if response.status_code == status.HTTP_201_CREATED:
        return {"message": "User registered successfully"}
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.text)


@app.post("/auth/login", tags=["users"])
async def login_user(user: UserLogin, tags=["users"]):
    print(f"{AUTH_SERVICE_URL}/auth/login*************")
    response = client.post(f"{AUTH_SERVICE_URL}/login", json=user.dict())
    if (response.status_code != 400 and response.headers["content-type"].strip().startswith("application/json")):
        try:
            return response.json()
        except ValueError:
            # decide how to handle a server that's misbehaving to this extent
            raise HTTPException(status_code=400, detail="Invalid credentials")
    else:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    
@app.get("/weather/{city}", response_model=WeatherResponse, tags=["weather"])
async def get_weather(city: str):
    response = client.get(f"{WEATHER_SERVICE_URL}/{city}")
    response.raise_for_status()
    return response.json()


# Define la clave secreta utilizada para firmar los tokens
SECRET_KEY = "secret"

# Logout endpoint
@app.post("/auth/logout", tags=["users"])
async def logout_user(user: UserToken, tags=["users"]):
    print(f"{AUTH_SERVICE_URL}/auth/logout********")
    response = client.post(f"{AUTH_SERVICE_URL}/logout", json=user.dict())
    if (response.status_code != 400 and response.headers["content-type"].strip().startswith("application/json")):
        try:
            return response.json()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid token")
    else:
        raise HTTPException(status_code=400, detail="Invalid token")
    
# Añade este endpoint para obtener los datos del usuario
@app.post("/auth/user-profile", tags=["users"])
async def get_user_profile(user: UserToken, tags=["users"]):
    print(f"{AUTH_SERVICE_URL}/auth/user-profile********")
    print(user)
    response = client.post(f"{AUTH_SERVICE_URL}/user-profile", json=user.dict())
    if (response.status_code != 400 and response.headers["content-type"].strip().startswith("application/json")):
        try:
            return response.json()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid token")
    else:
        raise HTTPException(status_code=400, detail="Invalid token")

# Endpoint para manejar operaciones de favoritos
@app.post("/auth/add_favorites", tags=["users"])
async def add_favorite(favorite_info: FavoritesRequest):
    print(f"{AUTH_SERVICE_URL}/auth/add_favorites**")
    try:
        # Envía la solicitud al microservicio de autenticación
        response = client.post(f"{AUTH_SERVICE_URL}/add_favorites", json={"token": favorite_info.token, **favorite_info.dict()})
        response.raise_for_status()  # Lanza una excepción si la solicitud no es exitosa

        return response.json()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/get_favorites", tags=["users"])
async def get_favorites(authorization: str = Header(...)):
    print(f"{AUTH_SERVICE_URL}/auth/get_favorites*")
    try:
        # Reenvía la solicitud al microservicio de autenticación
        response = client.get(f"{AUTH_SERVICE_URL}/get_favorites", headers={"Authorization": authorization})
        response.raise_for_status()  # Lanza una excepción si la solicitud no es exitosa

        return response.json()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auth/delete_favorite", tags=["users"])
async def delete_favorite(favorite_info: FavoritesRequest):
    print(f"{AUTH_SERVICE_URL}/auth/delete_favorite*")
    try:
        # Envía la solicitud al microservicio de autenticación
        response = client.post(f"{AUTH_SERVICE_URL}/delete_favorite", json={"token": favorite_info.token, **favorite_info.dict()})
        response.raise_for_status()  # Lanza una excepción si la solicitud no es exitosa

        return response.json()
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
