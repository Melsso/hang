FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY hang-frontend/package*.json ./

RUN npm ci

COPY hang-frontend/ .

RUN npm run build


FROM nginx:1.27.2

COPY --from=frontend-build /frontend/dist /usr/share/nginx/html

COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf