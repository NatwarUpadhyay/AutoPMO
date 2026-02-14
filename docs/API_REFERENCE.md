# API Reference
## REST API Documentation for AutoPMO

---

## Base URL
```
Production: https://api.autopmo.com/v1
Staging: https://api-staging.autopmo.com/v1
Local: http://localhost:8080/v1
```

## Authentication
All API requests require authentication using JWT Bearer tokens.

```bash
# Obtain token
curl -X POST https://sso.autopmo.com/auth/realms/autopmo/protocol/openid-connect/token \
  -d "client_id=autopmo-api" \
  -d "grant_type=password" \
  -d "username=your-email@company.com" \
  -d "password=your-password"

# Use token in requests
curl -H "Authorization: Bearer <your-jwt-token>" \
  https://api.autopmo.com/v1/projects
```

---

## Projects API

### List Projects
```http
GET /projects
```

**Query Parameters**:
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (planning, executing, closed)
- `search` (string): Search in project name/description

**Response**:
```json
{
  "data": [
    {
      "id": "proj_123abc",
      "name": "ERP Migration to AWS",
      "status": "executing",
      "budget": 500000.00,
      "start_date": "2024-02-01",
      "end_date": "2024-07-31",
      "completion_percentage": 45,
      "owner": {
        "id": "user_456def",
        "name": "John Smith",
        "email": "john.smith@company.com"
      }
    }
  ],
  "meta": {
    "total": 42,
    "page": 1,
    "per_page": 20,
    "total_pages": 3
  }
}
```

### Create Project
```http
POST /projects
```

**Request Body**:
```json
{
  "name": "New Cloud Migration Project",
  "description": "Migrate legacy ERP to Azure",
  "start_date": "2024-03-01",
  "end_date": "2024-09-30",
  "budget": 750000.00,
  "methodology": "hybrid",
  "stakeholders": [
    {"email": "cto@company.com", "role": "sponsor"},
    {"email": "pm@company.com", "role": "manager"}
  ]
}
```

**Response** (201 Created):
```json
{
  "id": "proj_789xyz",
  "name": "New Cloud Migration Project",
  "status": "planning",
  "created_at": "2024-02-14T10:30:00Z",
  "charter_url": "/projects/proj_789xyz/charter.pdf"
}
```

### Get Project
```http
GET /projects/{project_id}
```

### Update Project
```http
PATCH /projects/{project_id}
```

### Delete Project
```http
DELETE /projects/{project_id}
```

---

## Tasks API

### List Tasks
```http
GET /projects/{project_id}/tasks
```

### Create Task
```http
POST /projects/{project_id}/tasks
```

**Request Body**:
```json
{
  "title": "Migrate Finance Database",
  "description": "ETL from Oracle to PostgreSQL",
  "assigned_to": "user_alice",
  "due_date": "2024-03-15",
  "story_points": 13,
  "status": "todo",
  "dependencies": ["task_123", "task_456"]
}
```

---

## Agents API

### Invoke Orchestrator
```http
POST /agents/orchestrator/invoke
```

**Request Body**:
```json
{
  "project_id": "proj_123abc",
  "action": "create_migration_plan",
  "parameters": {
    "source_environment": "on-premise",
    "target_cloud": "aws",
    "app_type": "erp"
  }
}
```

**Response**:
```json
{
  "request_id": "req_xyz123",
  "status": "processing",
  "estimated_completion": "2024-02-14T10:35:00Z",
  "agent_chain": ["planning", "risk", "infrastructure"]
}
```

### Get Agent Status
```http
GET /agents/orchestrator/requests/{request_id}
```

---

## ML Models API

### Predict Risk Score
```http
POST /ml/models/risk-predictor/predict
```

**Request Body**:
```json
{
  "project_size": 500000,
  "team_experience": 7.5,
  "technology_maturity": 0.8,
  "dependency_count": 25,
  "stakeholder_count": 12,
  "budget_variance": 0.05,
  "schedule_variance": -0.10
}
```

**Response**:
```json
{
  "risk_score": 78,
  "risk_level": "high",
  "confidence": 0.92,
  "contributing_factors": [
    {"factor": "schedule_variance", "impact": 0.35},
    {"factor": "dependency_count", "impact": 0.28}
  ],
  "recommendations": [
    "Add buffer to critical path activities",
    "Consider dependency reduction strategies"
  ]
}
```

---

## Reports API

### Generate Status Report
```http
POST /reports/weekly-status
```

### Export Data
```http
GET /reports/export?format=excel&project_id=proj_123
```

---

## Webhooks API

### Register Webhook
```http
POST /webhooks
```

**Request Body**:
```json
{
  "url": "https://your-app.com/webhooks/autopmo",
  "events": ["project.created", "task.completed", "risk.escalated"],
  "secret": "your-webhook-secret"
}
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## Rate Limiting

- Standard: 1000 requests/hour
- Premium: 10,000 requests/hour

**Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 842
X-RateLimit-Reset: 1644845400
```

---

**Full interactive API documentation**: https://api.autopmo.com/docs
