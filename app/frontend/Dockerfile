# --- Stage 1: Build ---
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# --- Stage 2: Serve (Nginx) ---
FROM nginx:alpine
# Upgrade packages to patch vulnerabilities
RUN apk upgrade --no-cache libpng busybox

# Copy build artifacts to Nginx web root
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx config for React Router & Env Vars
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
