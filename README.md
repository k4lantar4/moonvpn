# MoonVPN 🌙

A Telegram bot and web dashboard for managing VPN accounts.

## Project Structure

```
moonvpn/
├── app/                    # Main application package
│   ├── api/               # API endpoints and routers
│   ├── bot/               # Telegram bot implementation
│   ├── core/              # Core functionality and configs
│   ├── db/                # Database models and migrations
│   ├── services/          # Business logic services
│   ├── schemas/           # Pydantic schemas
│   └── utils/             # Utility functions
├── docs/                  # Documentation
├── tests/                 # Test files
├── scripts/               # Utility scripts
└── docker/               # Docker configuration
```

## Features

- 🤖 Telegram bot for user interaction
- 🚀 FastAPI backend
- 📊 Admin dashboard
- 🔒 VPN account management
- 💳 Payment processing
- 📈 Server monitoring
- 🌐 Multi-language support

## Tech Stack

- Python 3.9+
- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- Docker
- Nginx

## Getting Started

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moonvpn.git
cd moonvpn
```

2. Copy the environment file and configure it:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the containers:
```bash
docker-compose up -d
```

## Development

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the development server:
```bash
uvicorn app.main:app --reload
```

## Testing

Run tests with pytest:
```bash
pytest
```

## Documentation

- API documentation: `/docs`
- Bot documentation: `docs/bot/`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
