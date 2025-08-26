# FFPU Backend API

FastAPI backend for the FFPU (Financial Futures Portfolio Utility) application.

## Features

- **Authentication System**: JWT-based authentication with Google OAuth support
- **Strategy Management**: Save, retrieve, and execute trading strategies
- **Database Integration**: SQLAlchemy ORM with PostgreSQL support
- **Email Services**: SMTP integration for user verification and password reset
- **RESTful API**: Clean, documented API endpoints

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (with SQLite fallback for development)
- **ORM**: SQLAlchemy
- **Authentication**: JWT, Google OAuth
- **Email**: SMTP with Jinja2 templates
- **Python Version**: 3.9+

## Project Structure

```
backend-repo/
├── app/
│   ├── auth/           # Authentication routes and services
│   ├── database/       # Database models and connection
│   ├── strategy/       # Strategy execution and management
│   ├── templates/      # Email templates
│   ├── __init__.py
│   └── main.py         # FastAPI application entry point
├── requirements.txt    # Python dependencies
└── README.md
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <your-backend-repo-url>
   cd backend-repo
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file with:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/ffpu_db
   SECRET_KEY=your-secret-key-here
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GOOGLE_REDIRECT_URI=http://localhost:3000/auth/google/callback
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ALGORITHM=HS256
   ```

## Running the Application

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/signup` - User registration
- `GET /api/auth/google/login` - Google OAuth login
- `POST /api/auth/forgot-password` - Password reset request
- `POST /api/auth/reset-password` - Password reset completion

### Strategy Management
- `POST /api/strategy/execute` - Execute trading strategy
- `POST /api/strategy/save` - Save new strategy
- `GET /api/strategy/get_all_public_strategies` - Get public strategies
- `GET /api/strategy/get_all_strategy_user` - Get user strategies
- `GET /api/strategy/strategies` - Get specific strategy

## Database Setup

### PostgreSQL (Production)
1. Install PostgreSQL
2. Create database: `CREATE DATABASE ffpu_db;`
3. Set `DATABASE_URL` in environment variables

### SQLite (Development)
For development, you can use SQLite by setting:
```env
DATABASE_URL=sqlite:///./ffpu.db
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license here]
