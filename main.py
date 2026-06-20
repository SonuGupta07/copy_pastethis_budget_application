version: "3.9"

services:
  backend:
    build:
      context: ./budget-management-backend
    container_name: budgetpro-backend
    env_file:
      - ./budget-management-backend/backend.env.docker
    ports:
      - "8000:8000"
    networks:
      - budget-net
    restart: unless-stopped

  frontend:
    build:
      context: ./budget-management-frontend
    container_name: budgetpro-frontend
    ports:
      - "5173:80"
    depends_on:
      - backend
    networks:
      - budget-net
    restart: unless-stopped

networks:
  budget-net:
    external: true
    ---------------------
    docker network create budget-net
    --------------
    docker network connect budget-net budget-oracle
    -------------
    docker rm -f budgetpro-frontend budgetpro-backend
    --------------
    docker start budget-oracle
    --------------
    docker compose up --build -d
    ------------
    