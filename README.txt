# ClimaNow

## Requirements

Make sure you have the following programs installed before you begin:
	- Python
	- Node.js
	- MySQL
	- MongoDB Compass

0)To startup the three containers that make the app, i.e. todo-fastapi-microservice, express-auth-api microservice and fastapi-gateway
docker-compose up 

If you need to rebuild the containers execute the command: docker-compose up --build --force-recreate --no-deps

docker compose up -d --no-deps --build main-app

The following steps would be carried out in case you want to start the containers manually: 

1) Start the microservice of Weather
cd todo-fastapi-microservice
pip install fastapi uvicorn httpx pymongo
uvicorn main:app --reload

2) Start the microservice of authentication
cd express-auth-api
npm install express bcryptjs jsonwebtoken swagger-ui-express yamljs mysql2 cors
mysql -u <usuario> -p<contraseña> < init.sql
node server.js

3) Start the gateway
cd fastapi-gateway
pip install fastapi uvicorn httpx PyJWT
uvicorn main:app --reload --port 8080
