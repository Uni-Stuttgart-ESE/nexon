# FROM continuumio/miniconda3:latest

# RUN pip install mlflow boto3 scikit-learn onnxruntime skl2onnx

# WORKDIR /app
# COPY . .

FROM python:3.13.5-slim-bookworm

WORKDIR /app

# Install dependencies for model generation and MLflow client
COPY . .
RUN pip install --no-cache-dir -r requirements.txt