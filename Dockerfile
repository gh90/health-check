# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .


RUN pip install -r requirements.txt
COPY . .

# 기본 커맨드는 compose에서 service마다 override
CMD ["python", "main.py"]