from fastapi import FastAPI, Request, HTTPException, Response
import httpx

app = FastAPI()

# Define the microservices URLs
WEATHER_SERVICE_URL = "http://localhost:8000"
USER_SERVICE_URL = "http://localhost:3000"

# HTTP Client
client = httpx.Client()

@app.api_route("/weather/{path:path}", methods=["GET"])
async def weather_service_proxy(path: str, request: Request):
    return await proxy_request(request, WEATHER_SERVICE_URL)

@app.api_route("/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def user_service_proxy(path: str, request: Request):
    return await proxy_request(request, USER_SERVICE_URL)

async def proxy_request(request: Request, service_url: str):
    method = request.method
    url = f"{service_url}/{request.url.path}"
    headers = dict(request.headers)
    content = await request.body()

    try:
        response = await client.request(method, url, headers=headers, content=content)
        if response.status_code == 400:
            # Handle Bad Request (e.g., invalid credentials)
            raise HTTPException(status_code=response.status_code, detail="Invalid credentials")
        
        return Response(content=response.content, status_code=response.status_code, headers=dict(response.headers.items()))
    
    except httpx.HTTPError as exc:
        # Handle general HTTP errors
        raise HTTPException(status_code=500, detail=str(exc))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("gateway:app", host="0.0.0.0", port=8080, reload=True)
