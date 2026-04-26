FROM node:18-alpine AS build

WORKDIR /projects

COPY web-player/package*.json web-player/
RUN cd web-player && npm install

COPY shared ./shared
COPY web-player ./web-player

WORKDIR /projects/web-player
RUN npm run build

FROM nginx:alpine

COPY --from=build /projects/web-player/dist /usr/share/nginx/html
COPY web-player/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
