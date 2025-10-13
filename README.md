
# NEXON

The **ONNX Deployment Platform** NEXON is a web-based application that allows users to upload, deploy, and run inference on ONNX models easily. It provides a user-friendly interface for managing AI models and executing inference tasks.

## 🚀 Features
- Upload and deploy ONNX models.
- Perform inference with custom input data.
- View inference results in a results panel.
- View all models uploaded on the platform and their metadata.
- Modern, responsive UI with an intuitive layout.
- 🆕 Deploy ONNX models directly from a MLflow Tracking Server

---

## Setup with MLflow

### 1. Setup environment variables
Copy `.env.example` and rename it to `.env`. For testing no value changes are needed, but it is adviced to change the passwords.

### 2. Start MLflow services
To build and start the MLflow Tracking Server, S3, MySQL and initial MLflow experiments use:
```bash
docker compose -f mlflow-compose.yml up --build -d
```

### 3. Start NEXON
To build and start the NEXON frontend, backend and MongoDB use:
```bash
docker compose -f nexon-compose.yml up --build -d
```

### 4. Use integration
- Check [MLflow](http://localhost:5000/#/models) to make sure the initial models are registered
- Run example requests from the `examples/` directory. 

```bash
curl -X POST http://localhost:8000/api/mlflow/sync -H "Content-Type: application/json" -d @examples/test_step_1.json
```
Optional, for better readable responses:
```bash
curl -X POST http://localhost:8000/api/mlflow/sync -H "Content-Type: application/json" -d @examples/test_step_1.json | python -m json.tool
```

- Check [NEXON](http://localhost:3000/overview) to see your deployed models 

---

## 📦 Installation

### **1. Clone the Repository**
```bash
git clone https://github.com/Uni-Stuttgart-ESE/nexon.git
cd nexon
```

### **2. Set Up MongoDB**
NEXON uses MongoDB to store uploaded models and their metadata.
#### 2.1 Install MongoDB
Mac: 
```bash
brew install mongodb-community@7.0
```
Ubuntu: 
```bash
sudo apt update
sudo apt install -y mongodb
```
Windows(Chocolatey): 
```bash
choco install mongodb
```
Or use your preferred package manager
#### 2.2 Start MongoDB Locally
```bash
mongod --dbpath=/data/db
```

### **3. Set Up the Backend**
Navigate to the server directory and create a virtual environment:
```bash
cd server
python -m venv nexon_env 
source nexon_env/bin/activate  # (Windows: nexon_env\Scripts\activate)
```
if this doesn't work try using ```python3```.

Install dependencies: 
```bash
pip install -r requirements.txt
```
Run the FastAPI backend:
```bash
uvicorn main:app --reload
```
### **4. Set Up the Frontend**
Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
npm install
npm start
```

