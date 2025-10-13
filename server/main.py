from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.inference import app as inference_app
from app.api.deployment import app as deployment_app
from app.api.upload import app as upload_app
from app.api.models import app as model_app
from app.api.mlflow_api import app as mlflow_app
from app.controller.database import close_mongo_connection, connect_to_mongo
import os 

# Load environment variables from .env
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to MongoDB when the app starts
    await connect_to_mongo()
    yield
    # Close MongoDB connection when the app stops
    await close_mongo_connection()

# Create the main FastAPI app
app = FastAPI(lifespan=lifespan)

# Mount the inference API to the main app (if modularized)
app.mount("/inference", inference_app)
app.mount("/deployment", deployment_app)
app.mount("/upload", upload_app)
app.mount("/api/mlflow", mlflow_app)
app.mount("/", model_app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Root endpoint (optional)
@app.get("/")
async def root():
    return {"message": "Welcome to the ONNX Inference API!"}



