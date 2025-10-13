# FROM ghcr.io/mlflow/mlflow:latest

# RUN pip install boto3

# CMD ["mlflow", "server", "-h", "0.0.0.0"]

FROM python:3.13.5-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y curl

# Install MLflow and any other dependencies needed by the server
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

# The command to run the server is defined in docker-compose.yml
# CMD ["mlflow", "server", "--host", "0.0.0.0", "--port", "5000", "--backend-store-uri", "sqlite:///mlflow.db", "--default-artifact-root", "/artifacts"]