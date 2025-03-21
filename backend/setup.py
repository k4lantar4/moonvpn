from setuptools import setup, find_packages

setup(
    name="moonvpn",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "alembic==1.13.1",
        "sqlalchemy==2.0.27",
        "asyncpg==0.30.0",
        "psycopg2-binary==2.9.9",
        "pydantic==2.10.6",
        "pydantic-settings==2.8.1",
        "python-dotenv==1.0.1",
        "fastapi==0.109.2",
        "uvicorn==0.27.1",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-multipart==0.0.9",
        "email-validator==2.1.0.post1",
        "redis==5.0.1",
        "aiohttp==3.9.3",
        "python-telegram-bot==20.8",
    ],
    python_requires=">=3.10",
) 