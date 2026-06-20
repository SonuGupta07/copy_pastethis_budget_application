# Step 1: Build React app
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Step 2: Serve built files with Nginx
FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
---------------------
node_modules
dist
.git
.gitignore
.env
Dockerfile
-------------------
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri /index.html;
    }
}
----------------------
docker run -d \
  --name budgetpro-frontend \
  -p 5173:80 \
  budgetpro-frontend:dev
  ----------------
  docker build -t budgetpro-frontend:dev ./budget-management-frontend
  -----------------------------------