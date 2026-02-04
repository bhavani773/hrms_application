# Agentic HR Documents Compliance System

An AI-powered HR document compliance system using the Blackboard Pattern with PostgreSQL, orchestrated by LangGraph, and powered by LangChain + Groq.

## Features

- **Blackboard Architecture**: PostgreSQL-backed centralized data store
- **AI-Powered Risk Assessment**: Uses Groq LLM for intelligent risk scoring
- **Automated Notifications**: SendGrid email integration for employee and admin alerts
- **Compliance Monitoring**: Tracks missing, expiring, and expired documents
- **RESTful API**: FastAPI-based endpoints for integration
- **Batch Processing**: Analyze multiple employees efficiently

## Architecture

- **Agents**: Modular agents for profile loading, requirements checking, compliance evaluation, risk scoring, reminder planning, and recommendations
- **LangGraph**: Orchestrates agent workflow in a directed graph
- **Blackboard**: Single source of truth for all data operations
- **SendGrid**: Email notification system

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Groq API key
- SendGrid API key (optional for testing)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-hr-docs-compliance
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your actual values
```

5. Set up PostgreSQL database:
```sql
CREATE DATABASE hr_docs;
```

### Environment Variables

Create a `.env` file with:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/hr_docs
GROQ_API_KEY=your_groq_key_here
SENDGRID_API_KEY=your_sendgrid_key_here
SENDGRID_FROM_EMAIL=noreply@company.com
ADMIN_EMAILS=hr-team@company.com,admin@company.com
```

## Usage

### Run FastAPI Server

```bash
uvicorn src.api.server:app --reload
```

The server will:
- Create database tables automatically
- Load 50+ dummy employees with realistic document scenarios
- Start the API server on http://localhost:8000

### API Endpoints

#### Run Document Compliance Scan

```bash
# Scan single employee
curl -X POST "http://localhost:8000/api/v1/run-docs-scan" \
  -H "Content-Type: application/json" \
  -d '{"employee_id": "650e8400-e29b-41d4-a716-446655440001"}'

# Batch scan (limit 25)
curl -X POST "http://localhost:8000/api/v1/run-docs-scan" \
  -H "Content-Type: application/json" \
  -d '{"batch": true, "limit": 25}'
```

#### Get Employee Results

```bash
curl "http://localhost:8000/api/v1/results/650e8400-e29b-41d4-a716-446655440001"
```

#### Get Dashboard Metrics

```bash
curl "http://localhost:8000/api/v1/dashboard/metrics"
```

#### Send Test Email

```bash
curl -X POST "http://localhost:8000/api/v1/send-test-email" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test email from the HR compliance system."
  }'
```

### Run Locally (Without Server)

```bash
python main.py
```

This will run a batch analysis on 10 employees and display results.

## System Components

### Agents

1. **CandidateProfileAgent**: Loads employee profile and documents
2. **RequirementsAgent**: Loads mandatory and role-specific document requirements
3. **ComplianceEvalAgent**: Evaluates compliance gaps and computes scores
4. **RiskScoringAgent**: AI-powered risk assessment using Groq
5. **ReminderPlannerAgent**: Creates reminders and sends notification emails
6. **RecommendationAgent**: Generates admin action plans and sends summary emails

### Database Schema

#### Core Tables
- `employees`: Employee master data
- `positions`: Job positions with document requirements
- `employee_documents`: Document records with status and expiry
- `document_requirements`: System-wide document requirements
- `compliance_requirements`: Compliance policies and thresholds

#### Output Tables
- `document_compliance_analysis`: AI-generated compliance analysis
- `document_reminders`: Document reminder records with email tracking

### Email Notifications

The system sends automated emails for:
- **Missing Documents**: Notifies employees of missing required documents
- **Expiring Documents**: Warns about documents expiring within threshold
- **Expired Documents**: Urgent notifications for expired documents
- **Admin Summaries**: Compliance reports sent to HR team

## Testing

### Acceptance Tests

The system includes built-in validation:

1. **Data Loading**: Verifies 50+ employees are loaded
2. **Compliance Analysis**: Creates analysis records for processed employees
3. **Reminder Creation**: Generates reminders for missing/expiring documents
4. **Email Integration**: Tests SendGrid email functionality
5. **Risk Assessment**: Validates AI-generated risk scores
6. **Dashboard Metrics**: Ensures metrics calculation works

### Manual Testing

1. Start the server: `uvicorn api.server:app --reload`
2. Visit http://localhost:8000/docs for interactive API documentation
3. Run batch scan: POST to `/api/v1/run-docs-scan` with `{"batch": true, "limit": 10}`
4. Check results: GET `/api/v1/dashboard/metrics`
5. Test email: POST to `/api/v1/send-test-email`

## Dummy Data

The system includes realistic dummy data:
- 50+ employees across multiple departments
- Various document statuses (pending, verified, expired)
- Realistic expiry dates and compliance scenarios
- Role-specific document requirements

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure PostgreSQL is running and credentials are correct
2. **Groq API**: Verify GROQ_API_KEY is set and valid
3. **SendGrid**: Check SENDGRID_API_KEY and FROM_EMAIL configuration
4. **Dependencies**: Run `pip install -r requirements.txt` to ensure all packages are installed

### Logs

The system provides detailed logging for each agent's execution. Check console output for:
- Agent execution progress
- Email send status
- Error messages and stack traces

## Development

### Adding New Agents

1. Extend `BaseAgent` class
2. Implement `run(state)` method
3. Add to LangGraph workflow in `controller.py`

### Extending Document Types

1. Add to `document_requirements` table
2. Update position-specific requirements
3. Modify compliance evaluation logic if needed

### Custom Email Templates

Modify email content in `ReminderPlannerAgent` and `RecommendationAgent` classes.

## License

This project is for demonstration purposes. Modify as needed for production use.