FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
# If package-lock exists, npm ci is best; fallback to install

# RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi <- commented out
ENV NPM_CONFIG_LEGACY_PEER_DEPS=true
RUN if [ -f package-lock.json ]; then npm ci; else npm install; fi

COPY . .

EXPOSE 5173
CMD ["sh", "-lc", "npm run dev -- --host 0.0.0.0 --port 5173"]
