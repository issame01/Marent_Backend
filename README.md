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
├── authentication/
├── backend_marent/
├── listing_system/
├── manage.py
├── media/
├── requirements.txt
├── staticfiles.py
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
git clone https://github.com/issame01/marent-backend.git

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


## System Requirements (Ubuntu)

Install the required system packages:

```bash
sudo apt update
sudo apt install libpq-dev python3-dev build-essential
```

### Then install the Python dependencies:

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

https://github.com/issame01/Marent_Frontend

---

## API Overview

Example endpoints:

| Method | Endpoint | Description |
|---------|----------|-------------|
| POST | `/api/authentication/register/` | Register a user |
| POST | `/api/authentication/login/` | Login |
| GET | `/api/authentication/verify-email` | Email verification |
| GET | `/api/profile/<str:username>//` | View profile |
| PUT | `/api/profile/update/` | Update profile|
| GET | `/api2/listings/` | View listing items |
| POST | `/api2/listings/create/` | Create an item |
| DELETE | `/api2/listings/<int:id>/delete/` | Delete an item |

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
