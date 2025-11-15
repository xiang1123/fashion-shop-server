# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Shanghai \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    WORKERS=2

# 可选：安装 tzdata（设置时区）与 curl（健康检查/调试可用）
RUN apt-get update && apt-get install -y --no-install-recommends tzdata curl \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先复制依赖清单，避免每次代码变更都重装依赖
COPY requirements.txt /app/requirements.txt

# 安装依赖
# 如遇到某些包编译失败，可临时安装编译工具：
# apt-get update && apt-get install -y build-essential python3-dev libffi-dev
RUN pip install --upgrade pip \
    && pip install -r /app/requirements.txt \
    && pip install gunicorn==21.2.0

# 复制应用代码
COPY app /app/app
COPY db /app/db

EXPOSE 8000

# 使用 gunicorn + uvicorn worker
CMD ["bash", "-lc", "gunicorn -k uvicorn.workers.UvicornWorker -w ${WORKERS} -b 0.0.0.0:8000 app.main:app"]