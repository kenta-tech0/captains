# ===== 共通ベース =====
FROM node:22-slim AS base
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1

# ===== 依存解決ステージ (キャッシュ層) =====
FROM base AS deps
COPY package*.json ./
RUN npm ci

# ===== 開発用ステージ (devcontainer が target に指定) =====
FROM base AS dev
ENV NODE_ENV=development
EXPOSE 3000
CMD ["npm", "run", "dev"]

# ===== ビルドステージ =====
FROM deps AS builder
ENV NODE_ENV=production
COPY . .
RUN npm run build

# ===== 本番ステージ (デフォルトターゲット) =====
FROM base AS prod
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["npm", "run", "start"]
