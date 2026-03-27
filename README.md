# AeroGuard AI Backend

A FastAPI-based backend system for pilot fatigue and risk assessment. This system evaluates pilot readiness based on sleep hours, duty hours, stress levels, and other metrics to determine risk levels.

## Features

- **Pilot Risk Assessment**: Calculate risk levels based on sleep, duty hours, and stress
- **Pilot Management**: Create, retrieve, and manage pilot records
- **Risk Level Filtering**: Query pilots by risk level (LOW, MEDIUM, HIGH)
- **RESTful API**: Clean and well-documented API endpoints
- **Database Integration**: PostgreSQL database with SQLAlchemy ORM

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **PostgreSQL**: Relational database
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server

## Prerequisites

- Python 3.8 or higher
- PostgreSQL database
- pip (Python package manager)

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory

2. **Create a virtual environment** (if not already created):
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Update the `DATABASE_URL` with your PostgreSQL credentials:
     ```
     DATABASE_URL=postgresql://username:password@host:port/database_name
     ```

6. **Create the database**:
   - Make sure PostgreSQL is running
   - Create a database named `aeroguard_db` (or update the DATABASE_URL accordingly)

## Running the Application

1. **Start the FastAPI server**:
   ```bash
   uvicorn main:app --reload
   ```

2. **Access the API**:
   - API Base URL: `http://localhost:8000`
   - Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`
   - Alternative API Documentation (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

### Health Check
- `GET /` - Root endpoint with API information
- `GET /health` - Health check endpoint

### Pilot Assessment
- `POST /assess/` - Assess a pilot's risk level
  - Request body includes: name, email, employee_id, sleep_hours, duty_hours, stress_level, reaction_score (optional), alertness_score (optional)
  - Returns: Assessment with calculated risk level

### Pilot Management
- `GET /pilots/` - Get all pilots (with pagination: `?skip=0&limit=100`)
- `GET /pilots/{pilot_id}` - Get pilot by ID
- `GET /pilots/employee/{employee_id}` - Get pilot by employee ID
- `GET /pilots/risk/{risk_level}` - Get pilots by risk level (LOW, MEDIUM, HIGH)

## Risk Calculation

The risk level is calculated using the following formula:

```
Risk Score = (8 - sleep_hours) * 2 + duty_hours * 1.5 + stress_level * 2
```

**Risk Levels:**
- **LOW**: Score < 10
- **MEDIUM**: 10 ≤ Score < 20
- **HIGH**: Score ≥ 20

## Example API Request

### Assess a Pilot
```bash
curl -X POST "http://localhost:8000/assess/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@airline.com",
    "employee_id": "EMP001",
    "sleep_hours": 6.5,
    "duty_hours": 8.0,
    "stress_level": 3.0,
    "reaction_score": 85.0,
    "alertness_score": 80.0
  }'
```

### Get All Pilots
```bash
curl -X GET "http://localhost:8000/pilots/"
```

### Get Pilots by Risk Level
```bash
curl -X GET "http://localhost:8000/pilots/risk/HIGH"
```

## Project Structure

```
aeroguard_backend/
├── main.py              # FastAPI application and routes
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic schemas for request/response validation
├── database.py          # Database configuration and connection
├── requirements.txt     # Python dependencies
├── .env.example        # Example environment variables
├── README.md           # Project documentation
├── DEVELOPMENT_ROADMAP.md  # Complete development roadmap with all phases
├── QUICK_START_GUIDE.md    # Quick start guide for immediate next steps
├── PROJECT_STRUCTURE.md    # Detailed project structure and organization
└── venv/               # Virtual environment (not committed)
```

## Documentation

- **DEVELOPMENT_ROADMAP.md**: Complete step-by-step roadmap breaking down all SRS requirements into actionable development phases
- **QUICK_START_GUIDE.md**: Quick reference for immediate next steps and common commands
- **PROJECT_STRUCTURE.md**: Detailed guide on project organization and best practices

## Development

### Running in Development Mode
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Migrations
Currently using SQLAlchemy's `create_all()` for table creation. For production, consider using Alembic for migrations.

## Future Enhancements

- [ ] Authentication and authorization
- [ ] Database migrations with Alembic
- [ ] Unit and integration tests
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Advanced risk calculation algorithms
- [ ] Historical data analysis
- [ ] Real-time monitoring and alerts

## License

This project is part of a Final Year Project.

## Contact

For questions or issues, please contact the development team.

