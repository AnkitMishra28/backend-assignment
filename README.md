
# Credit Approval System

## Overview
This project implements a Credit Approval System as specified in the internship assignment. It is built using Django 4+, Django REST Framework, Celery for background tasks, PostgreSQL for the database, and Docker for deployment. No frontend is required.

## Features Implemented
- **Django 4+ REST API**: All endpoints are built using Django REST Framework.
- **Models**: `Customer` and `Loan` models as per assignment attributes.
- **Background Data Ingestion**: Celery tasks ingest `customer_data.xlsx` and `loan_data.xlsx` into the database.
- **API Endpoints**:
  - `/register`: Register a new customer, auto-calculates approved limit.
  - `/check-eligibility`: Checks loan eligibility and corrects interest rate as per credit score and rules.
  - `/create-loan`: Processes new loan requests based on eligibility.
  - `/view-loan/<loan_id>`: View details of a specific loan and customer.
  - `/view-loans/<customer_id>`: View all current loans for a customer.
- **Database**: Uses PostgreSQL, configured for Docker Compose.
- **Celery & Redis**: For background ingestion tasks.
- **Dockerized**: All services (Django, PostgreSQL, Redis, Celery) run via a single `docker-compose up` command.
- **Admin Panel**: Models are registered for easy management.

## How to Deploy
1. Clone the repository:
   ```sh
   git clone https://github.com/AnkitMishra28/backend-project.git
   cd backend-project
   ```
2. Build and start all services:
   ```sh
   docker-compose up --build
   ```
3. Access the API at `http://localhost:8000/`.
4. To ingest Excel data, place `customer_data.xlsx` and `loan_data.xlsx` in the project root and trigger Celery tasks (see below).

## Ingesting Data
- Use Django admin or shell to trigger Celery tasks:
  ```python
  from core.tasks import ingest_customer_data, ingest_loan_data
  ingest_customer_data.delay('customer_data.xlsx')
  ingest_loan_data.delay('loan_data.xlsx')
  ```

## API Endpoints
- **POST /register**: Register a new customer
- **POST /check-eligibility**: Check loan eligibility
- **POST /create-loan**: Create a new loan
- **GET /view-loan/<loan_id>**: View loan details
- **GET /view-loans/<customer_id>**: View all loans for a customer

## Assignment Completion
All requirements from the assignment are implemented:
- Data models
- Background ingestion
- API endpoints with business logic and error handling
- Dockerized deployment
- PostgreSQL and Redis integration
- Admin registration

**Ready for submission.**
