# Authentication System

## Overview
The HRMS system now uses JWT token-based authentication instead of hardcoded credentials.

## Getting Started

### 1. Start the Server
```bash
uvicorn src.api.v1.server:app --reload
```

The server will automatically:
- Create database tables
- Seed basic employee data (4 employees)
- Initialize user accounts

### 2. Initialize User Accounts
```bash
curl -X POST "http://localhost:8000/api/v1/auth/init-users"
```

This creates user accounts for all employees with:
- Default password: `hrms2024`
- Role: `USER` (or `ADMIN` for HR Manager)

### 3. Login to Get JWT Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane.smith@company.com",
    "password": "hrms2024"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "user": {
    "email": "jane.smith@company.com",
    "full_name": "Jane Smith",
    "role": "ADMIN",
    "employee_id": "EMP002"
  },
  "expires_in": 1800
}
```

### 4. Use JWT Token for API Calls
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  "http://localhost:8000/api/v1/employees"
```

## Default Users
After initialization, you can login with:

| Employee | Email | Password | Role |
|----------|-------|----------|------|
| Jane Smith | jane.smith@company.com | hrms2024 | ADMIN |
| John Doe | john.doe@company.com | hrms2024 | USER |
| Mike Johnson | mike.johnson@company.com | hrms2024 | USER |
| Sarah Wilson | sarah.wilson@company.com | hrms2024 | USER |

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login with email/password
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/init-users` - Initialize user accounts

### Protected Endpoints (Require JWT Token)
- `GET /api/v1/employees` - Get all employees
- `GET /api/v1/dashboard/metrics` - Get dashboard metrics
- `POST /api/v1/run-docs-scan` - Run compliance scan
- `GET /api/v1/alerts` - Get compliance alerts
- All other API endpoints

## Security Features
- JWT tokens expire in 24 hours
- Passwords are hashed using SHA256
- All API endpoints require valid JWT token
- User roles (ADMIN/USER) for future authorization