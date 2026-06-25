FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY app/ app/
# 迁移服务（docker-compose 的 migrate）需要 alembic 配置与版本文件，否则
# `alembic upgrade head` 会因找不到配置/版本目录而失败。
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
