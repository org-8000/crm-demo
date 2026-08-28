# AgentOS 后端镜像
FROM python:3.13-slim

WORKDIR /app

# 系统依赖（psycopg 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir ".[serve]"

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.agent_os:app", "--host", "0.0.0.0", "--port", "8000"]
