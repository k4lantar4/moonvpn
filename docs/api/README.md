# MoonVPN API

A FastAPI-based REST API for the MoonVPN service.

## Features

- User authentication and authorization
- JWT token-based security
- Password reset functionality
- Email verification
- Database integration with SQLAlchemy
- CORS support
- API documentation with OpenAPI/Swagger

## Prerequisites

- Python 3.8+
- SQLite (or any other supported database)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moonvpn.git
cd moonvpn
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following variables:
```env
SECRET_KEY=your-secret-key-here
SQLALCHEMY_DATABASE_URI=sqlite:///./moonvpn.db
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

## Running the Application

1. Start the development server:
```bash
uvicorn main:app --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /api/v1/auth/login` - Login user
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-reset/confirm` - Confirm password reset
- `POST /api/v1/auth/password-change` - Change user password
- `POST /api/v1/auth/verify-email` - Verify user email
- `POST /api/v1/auth/refresh-token` - Refresh access token

## Development

### Project Structure

```
moonvpn/
├── api/
│   └── v1/
│       └── endpoints/
│           └── auth.py
├── core/
│   ├── config.py
│   ├── database/
│   │   ├── models/
│   │   └── session.py
│   └── schemas/
│       └── auth.py
├── main.py
├── requirements.txt
└── README.md
```

### Running Tests

```bash
pytest
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
