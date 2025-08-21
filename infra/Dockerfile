# Multi-stage image: Node build + Python sim
FROM node:20-alpine AS nodebuild
WORKDIR /app/mm
COPY code/mm/package.json code/mm/tsconfig.json ./
RUN npm i || true
COPY code/mm/src ./src
RUN npm run build || true

FROM python:3.11-slim AS pysim
WORKDIR /app/sim
COPY code/sim/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY code/sim .

FROM debian:stable-slim
WORKDIR /app
COPY --from=nodebuild /app/mm/dist /app/mm/dist
COPY --from=pysim /app/sim /app/sim
CMD ["bash","-lc","echo 'Run: python /app/sim/backtest.py' && python /app/sim/backtest.py"]
