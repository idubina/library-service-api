# Library Service API

Library Service API is a Django REST Framework application for managing books, users, borrowings, and Stripe payments. The project provides a browsable REST API for library management without a frontend.

- [Features](#features)
- [Technologies](#technologies)
- [Run with Docker](#run-with-docker)
- [Create Superuser](#create-superuser)
- [Run Tests](#run-tests)
- [API Documentation](#api-documentation)
- [Main Endpoints](#main-endpoints)
- [Permissions](#permissions)

## Features

- JWT authentication
- User registration and profile management
- Books CRUD
- Borrowing management
- Book return endpoint
- Borrowing filtering
- Stripe Checkout integration for payments
- Swagger API documentation
- Automated tests

## Technologies

- Python 3.12
- Django
- Django REST Framework
- PostgreSQL
- Docker & Docker Compose
- JWT Authentication (SimpleJWT)
- Stripe API

## Run with Docker

### Prerequisites

- Docker
- Docker Compose

### Installation

Clone the repository:

```bash
git clone https://github.com/idubina/library-service-api.git
cd library-service-api
```

Create a `.env` file based on `.env.sample`.

For Docker usage, keep:

```env
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

Build and start the containers:

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8001/
```

## Create Superuser

```bash
docker compose exec app python manage.py createsuperuser
```

## Run Tests

```bash
docker compose exec app python manage.py test
```

## API Documentation

Swagger documentation is available at:

```text
http://localhost:8001/api/doc/swagger/
```

Redoc documentation is available at:

```text
http://localhost:8001/api/doc/redoc/
```

## Main Endpoints

### Users

```text
POST   /api/users/                  Register user
POST   /api/users/token/            Obtain JWT tokens
POST   /api/users/token/refresh/    Refresh JWT token
GET    /api/users/me/               Get current user
PUT    /api/users/me/               Update current user
PATCH  /api/users/me/               Partial update current user
```

### Books

```text
GET     /api/library/books/
POST    /api/library/books/
GET     /api/library/books/<id>/
PUT     /api/library/books/<id>/
PATCH   /api/library/books/<id>/
DELETE  /api/library/books/<id>/
```

### Borrowings

```text
GET     /api/library/borrowings/
POST    /api/library/borrowings/
GET     /api/library/borrowings/<id>/
POST    /api/library/borrowings/<id>/return/
```

### Payments

```text
GET     /api/library/payments/success/
GET     /api/library/payments/cancel/
```

## Permissions

- Anyone can register and obtain JWT tokens.
- Authenticated users can manage their own borrowings.
- Only administrators can manage books.
- Only administrators can return borrowed books.
- Staff users can view borrowings of all users.