# Marent Backend

Marent Backend is the REST API powering the Marent marketplace application.

It provides authentication, user management, and item management for a platform where users can rent, exchange, or give away items they no longer need.

> **Project Status:** Development paused. This was a personal startup idea and is no longer actively maintained.

---

## Features

- User authentication
- User registration and login
- User profile management
- CRUD operations for item listings
- Image upload support
- Search and filtering
- RESTful API
- PostgreSQL database integration

---

## Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL
- Pillow
- Gunicorn

---

## Project Structure

```
marent-backend/
├── accounts/
├── listings/
├── users/
├── media/
├── config/
├── requirements.txt
├── manage.py
└── ...
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL
- pip
- virtualenv (recommended)

---

### Clone the repository

```bash
git clone https://github.com/<your-username>/marent-backend.git

cd marent-backend
```

---

### Create a virtual environment

```bash
python -m venv venv
```

Linux/macOS

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

---

### Install dependencies

```bash
pip install -r requirements.txt
```

---

### Configure environment variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your-secret-key

DEBUG=True

ALLOWED_HOSTS=localhost,127.0.0.1

DATABASE_URL=postgres://username:password@localhost:5432/marent

CORS_ALLOWED_ORIGINS=http://localhost:5173
```

> Do **not** commit your real `.env` file.

---

### Apply migrations

```bash
python manage.py migrate
```

---

### Create a superuser

```bash
python manage.py createsuperuser
```

---

### Run the development server

```bash
python manage.py runserver
```

The API will be available at

```
http://localhost:8000/
```

---

## Frontend

The frontend application is available in the companion repository:

**Marent Frontend**

https://github.com/<your-username>/marent

---

## API Overview

Example endpoints:

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/auth/register/` | Register a user |
| POST | `/api/auth/login/` | Login |
| GET | `/api/items/` | List items |
| POST | `/api/items/` | Create an item |
| GET | `/api/items/<id>/` | Retrieve an item |
| PUT | `/api/items/<id>/` | Update an item |
| DELETE | `/api/items/<id>/` | Delete an item |

*(Update these endpoints to match your project.)*

---

## What I Learned

Developing Marent Backend helped me strengthen my understanding of:

- Django architecture
- Django REST Framework
- REST API design
- Authentication
- PostgreSQL
- Database modeling
- File uploads
- CORS configuration
- Deployment

---

## Future Improvements

Some planned features include:

- JWT authentication
- Real-time chat
- Ratings and reviews
- Notifications
- Recommendation system
- Payment integration
- API documentation (Swagger/OpenAPI)

---

## License

This project is shared for educational and portfolio purposes.
