from fastapi import FastAPI, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException, Depends
from fastapi.openapi.models import HTTPBase
from datetime import datetime, timedelta
from pymongo import MongoClient
import httpx

app = FastAPI()

# Conexión a MongoDB
mongo_client = MongoClient('mongodb://localhost:27017/')
db = mongo_client['weather_cache']
cache_collection = db['weather_cache_collection']

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Define la URL de OpenWeatherMap
OPENWEATHERMAP_GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"
OPENWEATHERMAP_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = "5bae952342bff2da2e598e1f3d934d63"

# Función para obtener el cliente httpx
async def get_httpx_client():
    async with httpx.AsyncClient() as client:
        yield client

# Modelo para los datos meteorológicos
class WeatherData(BaseModel):
    temperature: float
    feels_like: float
    description: str
    city: str
    latitude: float
    longitude: float

# Modelo para la respuesta de la API de geolocalización
class GeoLocationResponse(BaseModel):
    lat: float
    lon: float

# Endpoint para obtener datos meteorológicos por ciudad
@app.get("/weather/{city}", response_model=WeatherData)
async def get_weather(city: str, client: httpx.AsyncClient = Depends(get_httpx_client)):
    try:
        # Obtener latitud y longitud de la ciudad usando la API de geolocalización de OpenWeatherMap
        geo_params = {
            "q": city,
            "limit": 1,
            "appid": API_KEY,
        }
        response = await client.get(OPENWEATHERMAP_GEO_URL, params=geo_params)
        response.raise_for_status()
        geo_data = response.json()

        print("Geolocation Data:", geo_data)  # Añadir log de depuración

        if not geo_data:
            raise HTTPException(status_code=404, detail=f"City '{city}' not found.")

        # Extraer latitud y longitud
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]
        print(lat)
        print(lon)

        # Comprobar si hay una entrada en la base de datos para esta ciudad en el último intervalo de tiempo
        cache_entry = cache_collection.find_one({"city": city, "timestamp": {"$gte": datetime.utcnow() - timedelta(minutes=20)}})

        if cache_entry:
            print("Retrieving data from MongoDB")
            # Si hay una entrada en la base de datos, devolver los datos almacenados
            return WeatherData(
                temperature=cache_entry["temperature"],
                feels_like=cache_entry["feels_like"],
                description=cache_entry["description"],
                city=city,
                latitude=lat,
                longitude=lon,
            )
        else:
            print("Fetching data from OpenWeatherMap API")
            # Obtener datos meteorológicos usando la latitud y longitud
            weather_params = {
                "lat": lat,
                "lon": lon,
                "appid": API_KEY,
                "units": "metric",
            }

            response = await client.get(OPENWEATHERMAP_WEATHER_URL, params=weather_params)
            response.raise_for_status()
            weather_data = response.json()

            print("Weather Data:", weather_data)  # Añadir log de depuración

            # Extraer datos relevantes de la respuesta de OpenWeatherMap
            temperature = weather_data["main"]["temp"]
            description = weather_data["weather"][0]["description"]
            feels_like = weather_data["main"]["feels_like"]

            print(temperature)
            print(feels_like)
            print(description)

            # Almacenar la nueva entrada en la base de datos
            cache_collection.insert_one({
                "city": city,
                "temperature": temperature,
                "feels_like": feels_like,
                "description": description,
                "timestamp": datetime.utcnow(),
            })

            return WeatherData(
                temperature=temperature,
                feels_like=feels_like,
                description=description,
                city=city,
                latitude=lat,
                longitude=lon,
            )

    except httpx.RequestError as exc:
        # Captura errores relacionados con solicitudes HTTP (por ejemplo, problemas de conexión)
        raise HTTPException(status_code=500, detail=f"Request error: {str(exc)}")
    except httpx.HTTPStatusError as exc:
        # Captura errores relacionados con códigos de estado HTTP no exitosos
        raise HTTPException(status_code=exc.response.status_code, detail=f"HTTP error: {str(exc)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
