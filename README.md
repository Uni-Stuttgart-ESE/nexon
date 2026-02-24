# NEXON

**NEXON** is an AI model deployment platform for **ONNX** models. It serves feature-parity **inference over REST and gRPC** behind an **Envoy** gateway. Models are stored in **MongoDB GridFS**, and both services share a single **inference orchestrator** with an **in-process LRU/TTL session cache**. All services are containerized and health-checked for reliable bring-up, benchmarking, and grading.
## 🚀 Features
<<<<<<< conflict 1 of 2
+++++++ wvouxtqy dc794b07 "Finalized robustness/performance scripts (all results PASS); align runners & compose; mark results as linguist-generated"
- Upload, deploy, list, and delete ONNX models.
- Deploy ONNX models directly from a MLflow Tracking Server
- Inference via REST and gRPC with identical request/response semantics.
- Inference endpoints
  - REST: `POST /inference/infer/{model_name}`
  - gRPC: `InferenceService/Predict` ([Full proto](server/grpc_service/protos/inference.proto))
> gRPC FQMN: `nexon.grpc.inference.v1.InferenceService/Predict`

- Envoy front door (single :8080 for REST + gRPC), admin UI on :9901.
- Health: REST `/healthz` (liveness), `/readyz` (readiness) and gRPC Health service.
- Frontend: the React UI invokes REST model management endpoints via Envoy on :8080.
- Shared components:
  - [Database (Motor + GridFS)](server/shared/database.py)
  - [Inference Orchestrator](server/shared/orchestrator.py)
  - [In-process Model Cache](server/shared/model_cache.py)
- Reproducible stubs: proto files are compiled into Python gRPC stubs at build time, packaged as a wheel, and installed.
- Modern, modular Python layout suitable for benchmarking and coursework.
- Docker containerization with health checks and multi-stage builds for gRPC stubs.

---

## 🔧 Prerequisites

**This project requires a running Docker environment.** <br>
Please follow the official guide for your operating system below:

### macOS
For macOS, install Docker Desktop.
- **Official Guide**: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)

### Linux
For Linux, install Docker Desktop or the Docker Engine suitable for your distribution.
- **Official Guide**: [Docker Desktop for Linux](https://docs.docker.com/desktop/install/linux-install/)
- **Official Guide**: [Docker Engine (by distribution)](https://docs.docker.com/engine/install/)

### Windows
A complete setup on Windows requires installing WSL, then Docker Desktop with the WSL 2 backend enabled.

1.  **Install WSL (Ubuntu)**: [Official Guide: Install WSL](https://learn.microsoft.com/windows/wsl/install)
2.  **Install Docker Desktop**: [Official Guide: Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
3.  **Enable WSL 2 Backend**: [Official Guide: Enable WSL 2 Backend](https://docs.docker.com/desktop/wsl/)

---

## 📦 Installation (Docker – recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/Uni-Stuttgart-ESE/nexon.git
cd nexon
```

### 2. Prepare Environment

Create `.env` at the repo root (copy from `.env.example`):

```bash
# PowerShell / bash / zsh (recommended)
docker run --rm -v "${PWD}:/w" alpine:3 sh -lc 'cp /w/.env.example /w/.env'
```

For testing no value changes are needed, but it is adviced to change the passwords.

Important keys:
- `NEXON_MONGO_DB`: database name (default: `onnx_platform`).
- `LOG_HEALTH`: `1` logs health probes; `0` suppresses noisy health access logs.
- `ENABLE_REFLECTION`: `1` to enable gRPC reflection (dev convenience).
- `GRPC_BIND`, `GRPC_MAX_RECV_BYTES`, `GRPC_MAX_SEND_BYTES`: advanced gRPC tuning.

### 3. Start MLflow services

To build and start the MLflow Tracking Server, S3, MySQL and initial MLflow experiments use:
```bash
docker compose -f mlflow-compose.yml up --build -d
```

### 4. Start NEXON
To build and start the NEXON frontend, backend and MongoDB use:
```bash
docker compose -f nexon-compose.yml up --build -d
```

### 5. Use integration
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

### 6. What's Running
- Envoy (gateway): `http://localhost:8080`
- REST API docs (via Envoy): `http://localhost:8080/docs`
- REST service (direct): `http://localhost:8000` (HTTP/1.1)
- gRPC service (direct): `localhost:50051` (HTTP/2)
- MongoDB: `localhost:27017`
- Envoy admin: `http://localhost:9901`

Status & logs:
```bash
docker compose ps
docker compose logs -f rest
docker compose logs -f grpc
docker compose logs -f envoy
```

Note: gRPC stubs are generated during the Docker build into `/app/server/stubs/`, packaged as a wheel, and installed into the image. They are not committed to git.

---

## 🧱 Local Development (optional)

> **Platform note**
> - **macOS/Linux:** run `make dev-bootstrap`.
> - **Windows:** use **WSL2 (Ubuntu)** and run the same `make` commands.

### 1) One-time dev setup

```bash
# from repo root
make dev-bootstrap
# - creates .env if missing (defaults)
# - creates .venv, installs runtime + dev deps
# - generates protobuf/gRPC stubs, builds & installs the wheel
# - installs the app in editable mode and runs sanity checks
```

### 2) Start services locally (separate terminals)

**MongoDB**
```bash
make run-mongo-native
```

**REST (FastAPI)**
```bash
make run-rest
```

**gRPC**
```bash
make run-grpc
```

**Envoy (local)**
```bash
# Uses localhost backends (8000/50051)
make run-envoy-dev
```

**Frontend (REST-only)**

```bash
cd frontend
npm install
npm start
# The UI calls REST model management endpoints (via Envoy on :8080).
```

> 🛠️ **Developer note (IDE imports)**
>
>The gRPC stubs (`inference_pb2*`) are generated inside the images. Your local IDE may still show unresolved imports if it isn’t using the container’s interpreter.
>- **Quick fix**: after `make dev-bootstrap`, point your IDE at `.venv/bin/python`
   > (On native Windows: `.venv\Scripts\python.exe`)
> <details>
> <summary><strong>IDE setup tips (optional)</strong></summary>
>
> - **PyCharm/IntelliJ:** `Settings` → `Project: Python Interpreter` → `Add` → `Existing` → select `.venv/bin/python`
> - **VS Code:** Command Palette → “Python: Select Interpreter” → choose `.venv`
>
> *No change is needed to run via Docker—this is just for editor IntelliSense.*
> </details>

## 🧩 Architecture at a Glance

```
nexon/
├─ ops/envoy/
│  ├─ envoy.compose.yaml     # Docker routing (service names: rest, grpc)
│  ├─ envoy.dev.yaml         # Local routing (localhost:8000 / :50051)
│  └─ logs/                  # access logs
├─ server/
│  ├─ rest/                  # FastAPI REST service; exposes /inference, /upload, /deployment
│  ├─ grpc_service/          # Async gRPC service; protos in ./protos; stubs packaged as a wheel at build time
│  ├─ shared/
│  │  ├─ database.py         # MongoDB (Motor) + GridFS clients
│  │  ├─ orchestrator.py     # shared inference orchestration
│  │  └─ model_cache.py      # ONNXRuntime session cache (LRU/TTL)
│  └─ tools/                 # CLI test clients & micro-benchmarks
└─ docker-compose.yml        # mongo + rest + grpc + envoy
```
---


## 🧪 Testing & Reproducibility

This project includes two primary guides for validation:

- **[NEXON: Test Client](server/tools/README.md)** <br>
  This guide provides a simple CLI client for smoke testing and micro-benchmarking. Use it for quick validation and running quick performance checks.
- **[NEXON: Local Testing & Evaluation Guide](server/tests/README.md)** <br>
  This is the primary guide for formal evaluation. It contains the **locally reproducible test suite** with scripts for generating key evidence artifacts referenced in the thesis.

---


## Acknowledgments

This work extends the original NEXON project by Hussein Megahed (UI and initial REST workflow).

Key contributions in this research extension:
- **gRPC Inference Service** — low-latency, high-throughput inference (establishes a foundation for multiple communication protocols)
- **Envoy gateway** — unified ingress on :8080
- **Shared components (used by both REST & gRPC):**
  - Centralized database module
  - Inference orchestrator
  - In-process model cache for ONNX Runtime sessions
- **REST workflow hardening** — added health/readiness, OpenAPI/Swagger documentation, modular sub-apps
- **Docker containerization** and a reproducible protobuf/gRPC stubs pipeline
