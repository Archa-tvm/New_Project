
project link-- http://localhost:8000/dashboard/
# FlowPulse - Business Operations & Workflow SaaS Platform

![FlowPulse Architecture](https://img.shields.io/badge/Architecture-Hybrid%20Microservices-6366f1?style=for-the-badge)
![Django](https://img.shields.io/badge/Django-5.0+-092e20?style=for-the-badge&logo=django&logoColor=white)
![C# .NET](https://img.shields.io/badge/.NET-8.0-512bd4?style=for-the-badge&logo=dotnet&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169e1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ed?style=for-the-badge&logo=docker&logoColor=white)

**FlowPulse** is an enterprise-grade Business Operations and Workflow Automation SaaS platform. It pairs the developer productivity, rich admin ecosystem, and multi-tenant security of **Django 5** with the raw execution speed, type safety, and concurrency of **C# .NET 8** as a dedicated state machine engine, backed by **PostgreSQL**.

---

## Architecture Overview

```
                                  +---------------------------------------+
                                  |            Users / Clients            |
                                  +-------------------+-------------------+
                                                      |
                                           HTTPS / REST / Web UI
                                                      |
                                                      v
                                  +---------------------------------------+
                                  |     Django SaaS Control Plane         |
                                  |  - Multi-tenant Auth & RBAC           |
                                  |  - Workflow Builder & Visualizer UI   |
                                  |  - RESTful APIs (Django REST Framework)|
                                  +--------+---------------------+--------+
                                           |                     |
                                    Trigger Event          Shared Data
                                           |                     |
                                           v                     v
+---------------------------------------+  |         +---------------------------+
|      .NET Core Workflow Engine        |<-+         |    PostgreSQL Database    |
|  - State Machine Runner (C#)          |            |  - Tenants & Users        |
|  - Step Executions & Rules Engine     +----------->|  - Workflow Definitions   |
|  - Async Background Worker & Webhooks |            |  - Instances & Step Logs  |
+---------------------------------------+            +---------------------------+
```

### Key Responsibilities

| Service | Technology | Role |
| :--- | :--- | :--- |
| **Control Plane** | Python 3.12 / Django 5 / DRF | Multi-tenancy, User Auth, RBAC, Blueprint Authoring, REST APIs, Tailwind Dashboard |
| **Workflow Engine** | C# / ASP.NET Core 8 / EF Core | State machine pipeline, condition branching, HTTP webhooks, SLA timers, polling worker |
| **Data Layer** | PostgreSQL 16 | Relational data store for tenants, definitions, step executions, audit trails |
| **Message Broker** | Redis 7 | Event routing and inter-service messaging |

---

## Directory Structure

```
saas-workflow-platform/
├── .github/
│   └── workflows/
│       └── ci.yml                     # Automated GitHub Actions test pipeline
├── backend-django/                    # Django SaaS Control Plane
│   ├── apps/
│   │   ├── tenants/                   # Multi-tenancy, memberships, audit logs
│   │   └── workflows/                 # Blueprint models, instances, approvals, UI
│   ├── core_config/                   # Django settings, URLs, WSGI
│   ├── templates/                     # Modern Tailwind CSS SaaS dashboards
│   ├── tests/                         # Pytest test suite
│   ├── Dockerfile
│   ├── manage.py
│   └── requirements.txt
├── engine-dotnet/                     # C# .NET Workflow Execution Engine
│   ├── FlowPulse.Engine/
│   │   ├── Controllers/               # Engine REST API (/api/v1/engine)
│   │   ├── Data/                      # EF Core PostgreSQL DbContext
│   │   ├── Models/                    # Shared database and graph schema entities
│   │   ├── Services/                  # State machine runner & node executors
│   │   ├── Workers/                   # Background polling worker
│   │   ├── Dockerfile
│   │   └── Program.cs
│   ├── FlowPulse.Engine.Tests/        # xUnit unit & integration tests
│   └── FlowPulse.Engine.sln
├── .env.example                       # Environment configuration template
├── .gitignore                         # Multi-stack gitignore
├── docker-compose.yml                 # Full stack container orchestrator
└── README.md
```

---

## Quickstart (Single Command)

### 1. Clone & Setup Environment
```bash
git clone <your-github-repo-url>
cd saas-workflow-platform
cp .env.example .env
```

### 2. Start Services via Docker Compose
```bash
docker compose up --build
```

Services will be initialized:
- **Django SaaS Dashboard & REST API**: [http://localhost:8000/dashboard/](http://localhost:8000/dashboard/)
- **Django Admin Panel**: [http://localhost:8000/admin/](http://localhost:8000/admin/) (Default: `admin` / `admin123`)
- **C# .NET Engine Swagger API**: [http://localhost:5050/swagger](http://localhost:5050/swagger)
- **PostgreSQL Database**: `localhost:5432` (DB: `flowpulse_db`)

---

## Core Features

### 1. Multi-Tenant Organization Management
- Tenant isolation with unique sub-organizations (`Apex Global Enterprise`, `Acme Corp`).
- Granular Role-Based Access Control: `Owner`, `Admin`, `Manager`, `Operator`, `Viewer`.
- Immutable audit trail capturing every workflow trigger and approval action.

### 2. Node-Based Workflow Automation Engine
Supported node types:
- **Trigger**: Ingestion of manual button clicks, webhooks, or business events.
- **Condition**: Dynamic boolean rule evaluations (`greater_than`, `less_than`, `equals`, thresholds).
- **HTTP Webhook**: Outbound REST calls with retry policies and response capture.
- **Approval Gate**: Human-in-the-loop task routing with Manager sign-off / rejection.
- **Notification**: Automated alerts dispatched across team communication channels.

### 3. Real-Time Operational Audit Log
Every workflow run generates a durable `WorkflowInstance` and discrete `StepExecution` records storing:
- Step status (`completed`, `in_progress`, `failed`, `skipped`)
- Millisecond-level duration benchmarks
- Complete input and output JSON payloads
- Error traces with automated fallback recovery

---

## REST API Reference

### Trigger a Workflow
```http
POST /api/v1/workflows/definitions/{workflow_id}/trigger/
Content-Type: application/json

{
  "payload": {
    "po_number": "PO-2026-991",
    "amount": 12500,
    "department": "Engineering"
  }
}
```

### Resolve an Approval Gate
```http
POST /api/v1/workflows/approvals/{task_id}/decide/
Content-Type: application/json

{
  "decision": "approved",
  "note": "Budget verified and approved for Q3."
}
```

### Query Engine Health
```http
GET /api/v1/workflows/engine/health/
```

---

## Local Development & Testing

### Running Django Locally
```bash
cd backend-django
python -m venv venv
# On Windows: venv\Scripts\activate | On Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py init_demo_data
python manage.py runserver 0.0.0.0:8000
```

### Running C# .NET Engine Locally
```bash
cd engine-dotnet
dotnet restore
dotnet build
dotnet test
dotnet run --project FlowPulse.Engine
```

---

## License
MIT License. Built with pride for scalable business process automation.
