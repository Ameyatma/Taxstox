# TaxStox Backend API

## Overview

TaxStox Backend is the FastAPI server powering the TaxStox ITR platform. It handles:

- **Authentication** (Google OAuth, JWT)
- **Tax filing** (ITR building, validation, PDF generation)
- **Market data** (stock information, charting, analyst data)
- **Enterprise features** (compliance, monitoring, scheduling)

## Key Features

### Authentication
- Google OAuth 2.0 integration
- JWT-based session management
- Password reset tokens
- Refresh token handling

### Tax Domain
- Dynamic ITR form generation
- Automated tax calculation
- PDF/JSON output generation
- Legal compliance checks

### Market Domain
- Stock search and discovery
- Real-time price data
- Charting and technical analysis
- Analyst consensus data

### Enterprise Features
- Audit logging
- Error monitoring
- Tenant isolation
- Scheduler for tax updates

## Database

The backend uses **SQLite** by default for development, with PostgreSQL support for production.

### Tables
- `users` - User accounts and authentication
- `filings` - Tax return submissions
- `tax_updates` - Latest tax regulations
- `tax_deadlines` - Important filing deadlines
- `tax_tips` - Tax-saving advice

## Technology Stack

### Backend
- **FastAPI** - API framework
- **SQLAlchemy** - ORM
- **PostgreSQL/SQLite** - Database
- **Redis** - Caching and session storage
- **Docker** - Containerization

### Frontend
- **Next.js 16.4.0** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+

### Installation

1. Clone the repository
2. Install Python dependencies
3. Set up environment variables
4. Install Node.js dependencies

### Running Locally

#### Backend API

```bash
cd apps/api
export $(cat .env | xargs)
python3 uvicorn-entrypoint.py
```

#### Frontend

```bash
cd apps/web
npm run dev
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/google/callback` - Google OAuth callback
- `POST /api/v1/auth/logout` - Logout

### Tax Filing
- `GET /api/v1/tax/filing` - Get filing form
- `POST /api/v1/tax/filing` - Submit filing
- `GET /api/v1/tax/info/{user_id}` - Get user tax info

### Market Data
- `GET /api/v1/market/stocks/search` - Search stocks
- `GET /api/v1/market/asset/{symbol}` - Get asset details
- `GET /api/v1/market/stocks/{symbol}/chart` - Get chart data

### Health Check
- `GET /api/v1/health` - Health check endpoint

## Development

### Testing

```bash
cd apps/api
python -m pytest tests/
```

### Database Migration

Automatic table creation with TimescaleDB support where available.

### Environment Variables

```env
DATABASE_URL=sqlite:///./test.db
TAXSTOX_JWT_SECRET=your-jwt-secret
TAXSTOX_ENCRYPTION_KEY=your-encryption-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## Docker

```bash
docker-compose up -d
```

## Production

See `deploy_gcp.sh` for Google Cloud Run deployment instructions.

## License

© 2026 TaxStox. All rights reserved.