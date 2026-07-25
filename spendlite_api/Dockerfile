# --- stage 1: build the single-page app -------------------------------------
FROM node:22-slim AS web

WORKDIR /web
COPY spendlite_web/package.json spendlite_web/package-lock.json ./
RUN npm ci
COPY spendlite_web/ ./
RUN npm run build

# --- stage 2: python runtime ------------------------------------------------
FROM python:3.12-slim

WORKDIR /app

COPY spendlite_api/requirements.txt api-requirements.txt
COPY spendlite_agent/requirements.txt agent-requirements.txt
RUN pip install --no-cache-dir -r api-requirements.txt -r agent-requirements.txt

COPY spendlite_api/ ./spendlite_api/
COPY spendlite_agent/ ./spendlite_agent/
COPY --from=web /web/dist ./static

EXPOSE 8000
CMD ["uvicorn", "spendlite_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
